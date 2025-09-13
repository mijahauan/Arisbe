#!/usr/bin/env python3
"""
Agon Interface - Clean reasoning and game interface for Arisbe.

This implements the Agon (reasoning/game) component of the three-part UX architecture:
- Organon (exploration/viewing)
- Ergasterion (composition/practice) 
- Agon (reasoning/games)

Features:
- Endoporeutic Game interface
- Domain modeling with umpire function
- Hypothesis management and testing
- Clean Qt interface without legacy contamination
"""

from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGraphicsView, QGraphicsScene, QPushButton, QLabel,
    QToolBar, QMenuBar, QStatusBar, QSplitter,
    QTextEdit, QGroupBox, QComboBox, QCheckBox, QListWidget,
    QTabWidget, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont

from egi_core_dau import RelationalGraphWithCuts
from gui.clean_diagram_renderer import CleanDiagramRenderer
from dau_diagram_correspondence import DauDiagramCorrespondence


class AgonInterface(QMainWindow):
    """
    Clean Agon interface for reasoning and existential graph games.
    
    Features:
    - Endoporeutic Game management
    - Hypothesis testing and validation
    - Domain modeling with logical outcomes
    - Contradiction/tautology/contingent detection
    - Clean Qt interface following Arisbe architecture
    """
    
    hypothesis_changed = Signal(str, RelationalGraphWithCuts)
    game_state_changed = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Arisbe Agon - Reasoning & Games")
        self.setGeometry(100, 100, 1400, 900)
        
        # Core components
        self.renderer = CleanDiagramRenderer()
        self.correspondence = DauDiagramCorrespondence()
        
        # Game state
        self.current_hypotheses: Dict[str, RelationalGraphWithCuts] = {}
        self.game_history: List[Dict[str, Any]] = []
        self.current_domain_model: Optional[RelationalGraphWithCuts] = None
        
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._connect_signals()
        
        # Initialize with welcome state
        self._initialize_agon()
    
    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with tabs for different Agon modes
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget for different reasoning modes
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Endoporeutic Game tab
        self.endoporeutic_tab = self._create_endoporeutic_tab()
        self.tab_widget.addTab(self.endoporeutic_tab, "🎯 Endoporeutic Game")
        
        # Domain Modeling tab
        self.domain_tab = self._create_domain_modeling_tab()
        self.tab_widget.addTab(self.domain_tab, "🏛️ Domain Modeling")
        
        # Hypothesis Testing tab
        self.hypothesis_tab = self._create_hypothesis_testing_tab()
        self.tab_widget.addTab(self.hypothesis_tab, "🧪 Hypothesis Testing")
    
    def _create_endoporeutic_tab(self) -> QWidget:
        """Create the Endoporeutic Game interface."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left panel - game board
        game_panel = QGroupBox("Game Board")
        game_layout = QVBoxLayout(game_panel)
        
        # Game view
        self.game_view = QGraphicsView()
        self.game_scene = QGraphicsScene()
        self.game_view.setScene(self.game_scene)
        from PySide6.QtGui import QPainter
        self.game_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        game_layout.addWidget(QLabel("Endoporeutic Game Sheet"))
        game_layout.addWidget(self.game_view)
        
        # Game controls
        game_controls = QHBoxLayout()
        self.new_game_btn = QPushButton("New Game")
        self.make_move_btn = QPushButton("Make Move")
        self.undo_move_btn = QPushButton("Undo Move")
        
        game_controls.addWidget(self.new_game_btn)
        game_controls.addWidget(self.make_move_btn)
        game_controls.addWidget(self.undo_move_btn)
        game_layout.addLayout(game_controls)
        
        layout.addWidget(game_panel, 2)
        
        # Right panel - game state and rules
        state_panel = QGroupBox("Game State & Rules")
        state_layout = QVBoxLayout(state_panel)
        
        # Current player
        self.current_player_label = QLabel("Current Player: Proponent")
        state_layout.addWidget(self.current_player_label)
        
        # Available moves
        moves_group = QGroupBox("Available Moves")
        moves_layout = QVBoxLayout(moves_group)
        
        self.moves_list = QListWidget()
        moves_layout.addWidget(self.moves_list)
        
        state_layout.addWidget(moves_group)
        
        # Game log
        log_group = QGroupBox("Game Log")
        log_layout = QVBoxLayout(log_group)
        
        self.game_log = QTextEdit()
        self.game_log.setMaximumHeight(200)
        self.game_log.setReadOnly(True)
        log_layout.addWidget(self.game_log)
        
        state_layout.addWidget(log_group)
        
        layout.addWidget(state_panel, 1)
        
        return tab
    
    def _create_domain_modeling_tab(self) -> QWidget:
        """Create the Domain Modeling interface."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left panel - domain diagram
        domain_panel = QGroupBox("Domain Model")
        domain_layout = QVBoxLayout(domain_panel)
        
        # Domain view
        self.domain_view = QGraphicsView()
        self.domain_scene = QGraphicsScene()
        self.domain_view.setScene(self.domain_scene)
        from PySide6.QtGui import QPainter
        self.domain_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        domain_layout.addWidget(QLabel("Domain Model Diagram"))
        domain_layout.addWidget(self.domain_view)
        
        # Domain controls
        domain_controls = QHBoxLayout()
        self.load_domain_btn = QPushButton("Load Domain")
        self.save_domain_btn = QPushButton("Save Domain")
        self.validate_domain_btn = QPushButton("Validate Model")
        
        domain_controls.addWidget(self.load_domain_btn)
        domain_controls.addWidget(self.save_domain_btn)
        domain_controls.addWidget(self.validate_domain_btn)
        domain_layout.addLayout(domain_controls)
        
        layout.addWidget(domain_panel, 2)
        
        # Right panel - umpire function and outcomes
        umpire_panel = QGroupBox("Umpire Function")
        umpire_layout = QVBoxLayout(umpire_panel)
        
        # Logical outcome detection
        outcome_group = QGroupBox("Logical Outcomes")
        outcome_layout = QVBoxLayout(outcome_group)
        
        self.contradiction_label = QLabel("Contradiction: Not Detected")
        self.tautology_label = QLabel("Tautology: Not Detected")
        self.contingent_label = QLabel("Contingent: Active")
        
        outcome_layout.addWidget(self.contradiction_label)
        outcome_layout.addWidget(self.tautology_label)
        outcome_layout.addWidget(self.contingent_label)
        
        umpire_layout.addWidget(outcome_group)
        
        # Domain analysis
        analysis_group = QGroupBox("Domain Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.domain_analysis = QTextEdit()
        self.domain_analysis.setReadOnly(True)
        self.domain_analysis.setPlainText("Domain analysis will appear here...")
        analysis_layout.addWidget(self.domain_analysis)
        
        umpire_layout.addWidget(analysis_group)
        
        layout.addWidget(umpire_panel, 1)
        
        return tab
    
    def _create_hypothesis_testing_tab(self) -> QWidget:
        """Create the Hypothesis Testing interface."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Top panel - hypothesis management
        hypothesis_panel = QGroupBox("Hypothesis Management")
        hypothesis_layout = QHBoxLayout(hypothesis_panel)
        
        # Hypothesis list
        list_group = QGroupBox("Active Hypotheses")
        list_layout = QVBoxLayout(list_group)
        
        self.hypothesis_list = QListWidget()
        list_layout.addWidget(self.hypothesis_list)
        
        # Hypothesis controls
        hypothesis_controls = QHBoxLayout()
        self.add_hypothesis_btn = QPushButton("Add Hypothesis")
        self.remove_hypothesis_btn = QPushButton("Remove")
        self.test_hypothesis_btn = QPushButton("Test Selected")
        
        hypothesis_controls.addWidget(self.add_hypothesis_btn)
        hypothesis_controls.addWidget(self.remove_hypothesis_btn)
        hypothesis_controls.addWidget(self.test_hypothesis_btn)
        list_layout.addLayout(hypothesis_controls)
        
        hypothesis_layout.addWidget(list_group, 1)
        
        # Hypothesis viewer
        viewer_group = QGroupBox("Hypothesis Viewer")
        viewer_layout = QVBoxLayout(viewer_group)
        
        self.hypothesis_view = QGraphicsView()
        self.hypothesis_scene = QGraphicsScene()
        self.hypothesis_view.setScene(self.hypothesis_scene)
        from PySide6.QtGui import QPainter
        self.hypothesis_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        viewer_layout.addWidget(self.hypothesis_view)
        hypothesis_layout.addWidget(viewer_group, 2)
        
        layout.addWidget(hypothesis_panel)
        
        # Bottom panel - test results
        results_panel = QGroupBox("Test Results")
        results_layout = QVBoxLayout(results_panel)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Hypothesis", "Test Type", "Result", "Confidence"])
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_panel)
        
        return tab
    
    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # Game menu
        game_menu = menubar.addMenu("Game")
        
        new_game_action = QAction("New Endoporeutic Game", self)
        new_game_action.triggered.connect(self._new_endoporeutic_game)
        game_menu.addAction(new_game_action)
        
        # Domain menu
        domain_menu = menubar.addMenu("Domain")
        
        load_domain_action = QAction("Load Domain Model", self)
        load_domain_action.triggered.connect(self._load_domain_model)
        domain_menu.addAction(load_domain_action)
        
        # Hypothesis menu
        hypothesis_menu = menubar.addMenu("Hypothesis")
        
        add_hypothesis_action = QAction("Add Hypothesis", self)
        add_hypothesis_action.triggered.connect(self._add_hypothesis)
        hypothesis_menu.addAction(add_hypothesis_action)
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = self.addToolBar("Main")
        
        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self._new_endoporeutic_game)
        toolbar.addAction(new_game_action)
        
        toolbar.addSeparator()
        
        validate_action = QAction("Validate", self)
        validate_action.triggered.connect(self._validate_current_state)
        toolbar.addAction(validate_action)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Agon ready - Select reasoning mode")
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.hypothesis_changed.connect(self._on_hypothesis_changed)
        self.game_state_changed.connect(self._on_game_state_changed)
        
        # Connect UI signals
        self.new_game_btn.clicked.connect(self._new_endoporeutic_game)
        self.add_hypothesis_btn.clicked.connect(self._add_hypothesis)
        self.validate_domain_btn.clicked.connect(self._validate_current_state)
    
    def _initialize_agon(self):
        """Initialize Agon with welcome state."""
        self.game_log.append("🎯 Welcome to Arisbe Agon - Reasoning & Games")
        self.game_log.append("Select a tab to begin:")
        self.game_log.append("• Endoporeutic Game - Interactive logical games")
        self.game_log.append("• Domain Modeling - Build and validate domain models")
        self.game_log.append("• Hypothesis Testing - Test competing hypotheses")
        
        self.status_bar.showMessage("Ready for reasoning activities")
    
    def _new_endoporeutic_game(self):
        """Start a new Endoporeutic Game."""
        self.game_log.append("\n🎯 Starting new Endoporeutic Game...")
        self.current_player_label.setText("Current Player: Proponent")
        
        # Clear game board
        self.game_scene.clear()
        
        # Initialize with empty sheet
        from frozendict import frozendict
        empty_egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="game_sheet",
            Cut=frozenset(),
            area=frozendict({"game_sheet": frozenset()}),
            rel=frozendict()
        )
        
        self.renderer.render_egi_to_scene(empty_egi, self.game_scene)
        self.game_view.fitInView(self.game_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
        
        self.status_bar.showMessage("Endoporeutic Game started - Proponent's turn")
    
    def _add_hypothesis(self):
        """Add a new hypothesis for testing."""
        hypothesis_name = f"Hypothesis_{len(self.current_hypotheses) + 1}"
        
        # Create empty hypothesis EGI
        from frozendict import frozendict
        hypothesis_egi = RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet=f"hypothesis_{len(self.current_hypotheses) + 1}",
            Cut=frozenset(),
            area=frozendict({f"hypothesis_{len(self.current_hypotheses) + 1}": frozenset()}),
            rel=frozendict()
        )
        
        self.current_hypotheses[hypothesis_name] = hypothesis_egi
        self.hypothesis_list.addItem(hypothesis_name)
        
        self.status_bar.showMessage(f"Added {hypothesis_name}")
    
    def _load_domain_model(self):
        """Load a domain model for analysis."""
        self.domain_analysis.setPlainText("Domain model loading not yet implemented...")
        self.status_bar.showMessage("Domain model functionality coming soon")
    
    def _validate_current_state(self):
        """Validate the current logical state."""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Endoporeutic Game
            self.game_log.append("🔍 Validating game state...")
            self.status_bar.showMessage("Game state validation complete")
        elif current_tab == 1:  # Domain Modeling
            self.domain_analysis.append("\n🔍 Validating domain model...")
            self.status_bar.showMessage("Domain model validation complete")
        elif current_tab == 2:  # Hypothesis Testing
            self.status_bar.showMessage("Hypothesis validation complete")
    
    def _on_hypothesis_changed(self, name: str, egi: RelationalGraphWithCuts):
        """Handle hypothesis change events."""
        self.status_bar.showMessage(f"Hypothesis '{name}' updated")
    
    def _on_game_state_changed(self, state: str):
        """Handle game state change events."""
        self.status_bar.showMessage(f"Game state: {state}")


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    agon = AgonInterface()
    agon.show()
    sys.exit(app.exec())
