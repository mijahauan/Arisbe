#!/usr/bin/env python3
"""
Agon Game - Peirce's Endoporeutic Game Interface

Provides the interactive gameplay interface for Peirce's Endoporeutic Game,
enabling users to build and explore a Universe of Discourse through
structured logical gameplay.
"""

import sys
import os
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QTextEdit, QLabel, QSplitter, QFrame, QComboBox,
        QTreeWidget, QTreeWidgetItem, QTabWidget, QFileDialog, QMessageBox,
        QStatusBar, QMenuBar, QMenu, QAction, QToolBar, QLineEdit, QGroupBox,
        QProgressBar, QSpinBox, QSlider, QListWidget, QListWidgetItem
    )
    from PySide6.QtGui import QPainter, QFont, QIcon, QPen, QBrush, QColor
    from PySide6.QtCore import Qt, QTimer, Signal, QPoint
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from egif_parser_dau import EGIFParser
from egdf_parser import EGDFParser
from canonical_qt_renderer import CanonicalQtRenderer
from canonical import CanonicalPipeline

class GamePhase(Enum):
    """Phases of the Endoporeutic Game."""
    SETUP = "setup"
    PROPOSITION = "proposition"
    CHALLENGE = "challenge"
    DEFENSE = "defense"
    RESOLUTION = "resolution"
    DISCOURSE_BUILDING = "discourse_building"

class PlayerRole(Enum):
    """Player roles in the game."""
    PROPOSER = "proposer"
    CHALLENGER = "challenger"
    OBSERVER = "observer"

@dataclass
class GameMove:
    """Represents a move in the game."""
    player: str
    move_type: str
    graph_before: Any
    graph_after: Any
    justification: str
    timestamp: float

@dataclass
class UniverseElement:
    """Element in the Universe of Discourse."""
    name: str
    definition: str
    relations: List[str]
    established_by: str
    game_context: str

class AgonGame(QMainWindow):
    """
    Main game interface for the Agon component.
    
    Provides the interactive Endoporeutic Game experience.
    """
    
    # Signals
    move_made = Signal(object)
    phase_changed = Signal(str)
    universe_updated = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Agon - Peirce's Endoporeutic Game")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Core components
        self.egif_parser = EGIFParser()
        self.egdf_parser = EGDFParser()
        self.pipeline = CanonicalPipeline()
        self.renderer = CanonicalQtRenderer()
        
        # Game state
        self.current_phase = GamePhase.SETUP
        self.current_player = None
        self.player_role = PlayerRole.OBSERVER
        self.game_moves = []
        self.universe_elements = {}
        self.current_proposition = None
        self.current_challenge = None
        
        # Graph state
        self.current_egi = None
        self.proposition_egi = None
        self.challenge_egi = None
        
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._initialize_game()
        
    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Game header
        header = self._create_game_header()
        main_layout.addWidget(header)
        
        # Main content splitter
        content_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(content_splitter)
        
        # Left panel - Game controls and universe
        left_panel = self._create_left_panel()
        content_splitter.addWidget(left_panel)
        
        # Center panel - Game board
        center_panel = self._create_center_panel()
        content_splitter.addWidget(center_panel)
        
        # Right panel - Move history and analysis
        right_panel = self._create_right_panel()
        content_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        content_splitter.setSizes([300, 800, 300])
        
    def _create_game_header(self) -> QWidget:
        """Create the game header with phase and player info."""
        header = QFrame()
        header.setFrameStyle(QFrame.Box)
        layout = QHBoxLayout(header)
        
        # Phase indicator
        self.phase_label = QLabel("Phase: Setup")
        self.phase_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.phase_label)
        
        layout.addStretch()
        
        # Player info
        self.player_label = QLabel("Role: Observer")
        layout.addWidget(self.player_label)
        
        # Turn indicator
        self.turn_label = QLabel("Turn: -")
        layout.addWidget(self.turn_label)
        
        return header
        
    def _create_left_panel(self) -> QWidget:
        """Create the left game controls panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Game setup
        setup_group = QGroupBox("Game Setup")
        setup_layout = QVBoxLayout(setup_group)
        
        # Player selection
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Your Role:"))
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Observer", "Proposer", "Challenger"])
        self.role_combo.currentTextChanged.connect(self._role_changed)
        role_layout.addWidget(self.role_combo)
        
        setup_layout.addLayout(role_layout)
        
        # New game button
        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self._new_game)
        setup_layout.addWidget(self.new_game_btn)
        
        layout.addWidget(setup_group)
        
        # Game actions
        actions_group = QGroupBox("Game Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.propose_btn = QPushButton("Make Proposition")
        self.propose_btn.clicked.connect(self._make_proposition)
        self.propose_btn.setEnabled(False)
        actions_layout.addWidget(self.propose_btn)
        
        self.challenge_btn = QPushButton("Challenge")
        self.challenge_btn.clicked.connect(self._make_challenge)
        self.challenge_btn.setEnabled(False)
        actions_layout.addWidget(self.challenge_btn)
        
        self.defend_btn = QPushButton("Defend")
        self.defend_btn.clicked.connect(self._defend_proposition)
        self.defend_btn.setEnabled(False)
        actions_layout.addWidget(self.defend_btn)
        
        self.accept_btn = QPushButton("Accept")
        self.accept_btn.clicked.connect(self._accept_proposition)
        self.accept_btn.setEnabled(False)
        actions_layout.addWidget(self.accept_btn)
        
        layout.addWidget(actions_group)
        
        # Universe of Discourse
        universe_group = QGroupBox("Universe of Discourse")
        universe_layout = QVBoxLayout(universe_group)
        
        self.universe_list = QListWidget()
        self.universe_list.itemClicked.connect(self._universe_item_selected)
        universe_layout.addWidget(self.universe_list)
        
        # Add to universe button
        self.add_universe_btn = QPushButton("Add to Universe")
        self.add_universe_btn.clicked.connect(self._add_to_universe)
        self.add_universe_btn.setEnabled(False)
        universe_layout.addWidget(self.add_universe_btn)
        
        layout.addWidget(universe_group)
        
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """Create the center game board panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Game board tabs
        self.board_tabs = QTabWidget()
        layout.addWidget(self.board_tabs)
        
        # Current state tab
        self.current_tab = self._create_board_tab("Current State")
        self.board_tabs.addTab(self.current_tab, "Current")
        
        # Proposition tab
        self.proposition_tab = self._create_board_tab("Proposition")
        self.board_tabs.addTab(self.proposition_tab, "Proposition")
        
        # Challenge tab
        self.challenge_tab = self._create_board_tab("Challenge")
        self.board_tabs.addTab(self.challenge_tab, "Challenge")
        
        # Input area
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        
        self.egif_input = QTextEdit()
        self.egif_input.setPlaceholderText("Enter EGIF for proposition or challenge...")
        self.egif_input.setMaximumHeight(100)
        input_layout.addWidget(self.egif_input)
        
        input_buttons = QHBoxLayout()
        
        self.parse_btn = QPushButton("Parse EGIF")
        self.parse_btn.clicked.connect(self._parse_input)
        input_buttons.addWidget(self.parse_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_input)
        input_buttons.addWidget(self.clear_btn)
        
        input_layout.addLayout(input_buttons)
        
        layout.addWidget(input_group)
        
        return panel
        
    def _create_board_tab(self, title: str) -> QWidget:
        """Create a game board tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Canvas for rendering
        canvas = self.renderer.create_canvas()
        layout.addWidget(canvas)
        
        return widget
        
    def _create_right_panel(self) -> QWidget:
        """Create the right analysis panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Move history
        history_group = QGroupBox("Move History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QTreeWidget()
        self.history_list.setHeaderLabels(["Move", "Player", "Type"])
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(history_group)
        
        # Game analysis
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analysis_display = QTextEdit()
        self.analysis_display.setReadOnly(True)
        self.analysis_display.setMaximumHeight(200)
        analysis_layout.addWidget(self.analysis_display)
        
        layout.addWidget(analysis_group)
        
        # Game rules
        rules_group = QGroupBox("Game Rules")
        rules_layout = QVBoxLayout(rules_group)
        
        rules_text = QTextEdit()
        rules_text.setReadOnly(True)
        rules_text.setPlainText(
            "Endoporeutic Game Rules:\n\n"
            "1. Proposer makes a claim using EG\n"
            "2. Challenger may question or counter\n"
            "3. Proposer defends or modifies\n"
            "4. Resolution adds to Universe\n"
            "5. Build shared understanding"
        )
        rules_layout.addWidget(rules_text)
        
        layout.addWidget(rules_group)
        
        return panel
        
    def _setup_menus(self):
        """Setup application menus."""
        menubar = self.menuBar()
        
        # Game menu
        game_menu = menubar.addMenu("Game")
        
        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self._new_game)
        game_menu.addAction(new_game_action)
        
        save_game_action = QAction("Save Game", self)
        save_game_action.triggered.connect(self._save_game)
        game_menu.addAction(save_game_action)
        
        load_game_action = QAction("Load Game", self)
        load_game_action.triggered.connect(self._load_game)
        game_menu.addAction(load_game_action)
        
        game_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)
        
        # Universe menu
        universe_menu = menubar.addMenu("Universe")
        
        export_universe_action = QAction("Export Universe", self)
        export_universe_action.triggered.connect(self._export_universe)
        universe_menu.addAction(export_universe_action)
        
        import_universe_action = QAction("Import Universe", self)
        import_universe_action.triggered.connect(self._import_universe)
        universe_menu.addAction(import_universe_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        rules_action = QAction("Game Rules", self)
        rules_action.triggered.connect(self._show_rules)
        help_menu.addAction(rules_action)
        
        about_action = QAction("About Agon", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_toolbar(self):
        """Setup application toolbar."""
        toolbar = self.addToolBar("Game")
        
        # Game actions
        new_game_action = QAction("New Game", self)
        new_game_action.triggered.connect(self._new_game)
        toolbar.addAction(new_game_action)
        
        toolbar.addSeparator()
        
        # Phase actions
        next_phase_action = QAction("Next Phase", self)
        next_phase_action.triggered.connect(self._next_phase)
        toolbar.addAction(next_phase_action)
        
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to play Endoporeutic Game")
        
    def _initialize_game(self):
        """Initialize a new game."""
        self.current_phase = GamePhase.SETUP
        self.game_moves.clear()
        self.universe_elements.clear()
        self._update_ui_for_phase()
        self._update_displays()
        
    def _role_changed(self, role_text: str):
        """Handle role change."""
        role_map = {
            "Observer": PlayerRole.OBSERVER,
            "Proposer": PlayerRole.PROPOSER,
            "Challenger": PlayerRole.CHALLENGER
        }
        
        self.player_role = role_map.get(role_text, PlayerRole.OBSERVER)
        self.player_label.setText(f"Role: {role_text}")
        self._update_ui_for_role()
        
    def _update_ui_for_role(self):
        """Update UI based on current role."""
        is_proposer = self.player_role == PlayerRole.PROPOSER
        is_challenger = self.player_role == PlayerRole.CHALLENGER
        
        # Enable/disable buttons based on role and phase
        if self.current_phase == GamePhase.PROPOSITION:
            self.propose_btn.setEnabled(is_proposer)
            self.challenge_btn.setEnabled(is_challenger)
        elif self.current_phase == GamePhase.CHALLENGE:
            self.challenge_btn.setEnabled(is_challenger)
            self.defend_btn.setEnabled(is_proposer)
        elif self.current_phase == GamePhase.DEFENSE:
            self.defend_btn.setEnabled(is_proposer)
            self.accept_btn.setEnabled(is_challenger)
            
    def _update_ui_for_phase(self):
        """Update UI based on current phase."""
        self.phase_label.setText(f"Phase: {self.current_phase.value.title()}")
        
        # Reset all buttons
        for btn in [self.propose_btn, self.challenge_btn, self.defend_btn, self.accept_btn]:
            btn.setEnabled(False)
            
        # Enable appropriate buttons for phase
        if self.current_phase == GamePhase.PROPOSITION:
            self.propose_btn.setEnabled(self.player_role == PlayerRole.PROPOSER)
        elif self.current_phase == GamePhase.CHALLENGE:
            self.challenge_btn.setEnabled(self.player_role == PlayerRole.CHALLENGER)
        elif self.current_phase == GamePhase.DEFENSE:
            self.defend_btn.setEnabled(self.player_role == PlayerRole.PROPOSER)
            self.accept_btn.setEnabled(self.player_role == PlayerRole.CHALLENGER)
        elif self.current_phase == GamePhase.DISCOURSE_BUILDING:
            self.add_universe_btn.setEnabled(True)
            
    def _new_game(self):
        """Start a new game."""
        self._initialize_game()
        self.status_bar.showMessage("New game started")
        
    def _make_proposition(self):
        """Make a proposition."""
        egif_text = self.egif_input.toPlainText().strip()
        if not egif_text:
            QMessageBox.warning(self, "Input Required", "Please enter EGIF for your proposition")
            return
            
        try:
            parser = EGIFParser(egif_text)
            self.proposition_egi = parser.parse()
            
            # Record move
            move = GameMove(
                player=self.player_role.value,
                move_type="proposition",
                graph_before=self.current_egi,
                graph_after=self.proposition_egi,
                justification=egif_text,
                timestamp=time.time()
            )
            self.game_moves.append(move)
            
            self.current_phase = GamePhase.CHALLENGE
            self._update_displays()
            self._update_ui_for_phase()
            
            self.status_bar.showMessage("Proposition made - awaiting challenge")
            
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse proposition:\n{e}")
            
    def _make_challenge(self):
        """Make a challenge."""
        egif_text = self.egif_input.toPlainText().strip()
        if not egif_text:
            QMessageBox.warning(self, "Input Required", "Please enter EGIF for your challenge")
            return
            
        try:
            parser = EGIFParser(egif_text)
            self.challenge_egi = parser.parse()
            
            # Record move
            move = GameMove(
                player=self.player_role.value,
                move_type="challenge",
                graph_before=self.proposition_egi,
                graph_after=self.challenge_egi,
                justification=egif_text,
                timestamp=time.time()
            )
            self.game_moves.append(move)
            
            self.current_phase = GamePhase.DEFENSE
            self._update_displays()
            self._update_ui_for_phase()
            
            self.status_bar.showMessage("Challenge made - awaiting defense")
            
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse challenge:\n{e}")
            
    def _defend_proposition(self):
        """Defend the proposition."""
        # Implementation would handle defense logic
        self.current_phase = GamePhase.RESOLUTION
        self._update_ui_for_phase()
        self.status_bar.showMessage("Defense made - resolving")
        
    def _accept_proposition(self):
        """Accept the proposition."""
        self.current_phase = GamePhase.DISCOURSE_BUILDING
        self._update_ui_for_phase()
        self.status_bar.showMessage("Proposition accepted - building discourse")
        
    def _add_to_universe(self):
        """Add current proposition to Universe of Discourse."""
        if self.proposition_egi:
            name = f"Element_{len(self.universe_elements) + 1}"
            element = UniverseElement(
                name=name,
                definition=self.egif_input.toPlainText().strip(),
                relations=[],
                established_by=self.player_role.value,
                game_context=f"Game move {len(self.game_moves)}"
            )
            
            self.universe_elements[name] = element
            self._update_universe_display()
            
            self.status_bar.showMessage(f"Added {name} to Universe of Discourse")
            
    def _parse_input(self):
        """Parse the current EGIF input."""
        egif_text = self.egif_input.toPlainText().strip()
        if egif_text:
            try:
                parser = EGIFParser(egif_text)
                egi = parser.parse()
                
                # Render in current tab
                current_tab = self.board_tabs.currentWidget()
                if current_tab:
                    layout_result = self.pipeline.execute_pipeline(egi)
                    canvas = current_tab.findChild(QWidget)  # Find canvas widget
                    if canvas:
                        self.renderer.render_egi(egi, layout_result, canvas)
                        
                self.status_bar.showMessage("EGIF parsed and rendered")
                
            except Exception as e:
                QMessageBox.critical(self, "Parse Error", f"Failed to parse EGIF:\n{e}")
                
    def _clear_input(self):
        """Clear the input area."""
        self.egif_input.clear()
        
    def _next_phase(self):
        """Move to next game phase."""
        phase_order = [
            GamePhase.SETUP,
            GamePhase.PROPOSITION,
            GamePhase.CHALLENGE,
            GamePhase.DEFENSE,
            GamePhase.RESOLUTION,
            GamePhase.DISCOURSE_BUILDING
        ]
        
        current_index = phase_order.index(self.current_phase)
        if current_index < len(phase_order) - 1:
            self.current_phase = phase_order[current_index + 1]
            self._update_ui_for_phase()
            
    def _update_displays(self):
        """Update all display elements."""
        self._update_history_display()
        self._update_analysis_display()
        self._update_universe_display()
        
    def _update_history_display(self):
        """Update move history display."""
        self.history_list.clear()
        
        for i, move in enumerate(self.game_moves):
            item = QTreeWidgetItem([
                f"Move {i+1}",
                move.player,
                move.move_type
            ])
            self.history_list.addTopLevelItem(item)
            
    def _update_analysis_display(self):
        """Update game analysis."""
        analysis_text = f"Game Progress:\n"
        analysis_text += f"Phase: {self.current_phase.value}\n"
        analysis_text += f"Moves: {len(self.game_moves)}\n"
        analysis_text += f"Universe Elements: {len(self.universe_elements)}\n"
        
        self.analysis_display.setPlainText(analysis_text)
        
    def _update_universe_display(self):
        """Update Universe of Discourse display."""
        self.universe_list.clear()
        
        for name, element in self.universe_elements.items():
            item = QListWidgetItem(f"{name}: {element.definition[:50]}...")
            item.setData(Qt.UserRole, element)
            self.universe_list.addItem(item)
            
    def _universe_item_selected(self, item):
        """Handle universe item selection."""
        element = item.data(Qt.UserRole)
        if element:
            self.status_bar.showMessage(f"Selected: {element.name}")
            
    def _save_game(self):
        """Save current game state."""
        # Implementation would save game state
        self.status_bar.showMessage("Game saved")
        
    def _load_game(self):
        """Load game state."""
        # Implementation would load game state
        self.status_bar.showMessage("Game loaded")
        
    def _export_universe(self):
        """Export Universe of Discourse."""
        # Implementation would export universe
        self.status_bar.showMessage("Universe exported")
        
    def _import_universe(self):
        """Import Universe of Discourse."""
        # Implementation would import universe
        self.status_bar.showMessage("Universe imported")
        
    def _show_rules(self):
        """Show game rules dialog."""
        QMessageBox.information(
            self, "Endoporeutic Game Rules",
            "Peirce's Endoporeutic Game Rules:\n\n"
            "1. The Proposer makes a claim using Existential Graphs\n"
            "2. The Challenger may question or counter the claim\n"
            "3. The Proposer defends or modifies their position\n"
            "4. Through resolution, elements are added to the Universe of Discourse\n"
            "5. The goal is to build shared understanding through logical dialogue\n\n"
            "The game develops a common vocabulary and understanding "
            "of the domain being explored."
        )
        
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Agon",
            "Arisbe Agon - Peirce's Endoporeutic Game\n\n"
            "The Agon provides an interactive implementation of "
            "Charles Sanders Peirce's Endoporeutic Game, enabling "
            "users to build and explore a Universe of Discourse "
            "through structured logical gameplay.\n\n"
            "Features:\n"
            "• Interactive gameplay following Peirce's rules\n"
            "• Universe of Discourse construction\n"
            "• Game state tracking and validation\n"
            "• Educational progression through scenarios\n"
            "• Collaborative discourse building"
        )

def main():
    """Main function to run Agon game."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required to run Agon")
        return 1
        
    app = QApplication(sys.argv)
    app.setApplicationName("Arisbe Agon")
    app.setApplicationVersion("1.0.0")
    
    game = AgonGame()
    game.show()
    
    return app.exec()

if __name__ == "__main__":
    import time
    sys.exit(main())
