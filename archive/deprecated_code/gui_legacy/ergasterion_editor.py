#!/usr/bin/env python3
"""
Ergasterion Editor - Clean Qt-based EGI composition and practice interface.

This is the main Ergasterion component for rule-governed graph building,
following the clean architecture principles.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from dau_diagram_correspondence import DauDiagramCorrespondence
from egi_core_dau import RelationalGraphWithCuts
from formal_transformation_rules import FormalTransformationRule, TransformationContext
from gui.clean_diagram_renderer import CleanDiagramRenderer


class ErgasterionEditor(QMainWindow):
    """
    Clean Ergasterion editor for rule-governed EGI composition and practice.

    Features:
    - Empty sheet starting context
    - Rule-governed transformation sequences
    - Graph building through valid EG transformations
    - Practice mode with transformation validation
    - Clean Qt interface without legacy contamination
    """

    graph_changed = Signal(RelationalGraphWithCuts)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Arisbe Ergasterion - EGI Workshop")
        self.setGeometry(100, 100, 1200, 800)

        # Core components
        self.current_egi: Optional[RelationalGraphWithCuts] = None
        self.renderer = CleanDiagramRenderer()
        self.correspondence = DauDiagramCorrespondence()

        # Transformation state
        self.transformation_history: List[RelationalGraphWithCuts] = []
        self.available_transformations: List[FormalTransformationRule] = []

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._connect_signals()

        # Start with empty sheet
        self._initialize_empty_sheet()

    def _setup_ui(self):
        """Set up the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QVBoxLayout())
        central_widget.layout().addWidget(main_splitter)

        # Left panel - diagram view
        diagram_panel = self._create_diagram_panel()
        main_splitter.addWidget(diagram_panel)

        # Right panel - controls and history
        control_panel = self._create_control_panel()
        main_splitter.addWidget(control_panel)

        # Set splitter proportions
        main_splitter.setSizes([800, 400])

    def _create_diagram_panel(self) -> QWidget:
        """Create the main diagram viewing panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Diagram view
        self.diagram_view = QGraphicsView()
        self.diagram_scene = QGraphicsScene()
        self.diagram_view.setScene(self.diagram_scene)
        from PySide6.QtGui import QPainter

        self.diagram_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout.addWidget(QLabel("Sheet of Assertion"))
        layout.addWidget(self.diagram_view)

        return panel

    def _create_control_panel(self) -> QWidget:
        """Create the control and history panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Transformation controls
        transform_group = QGroupBox("Available Transformations")
        transform_layout = QVBoxLayout(transform_group)

        self.transform_buttons = {}
        for rule_name in [
            "Insert Vertex",
            "Insert Double Cut",
            "Erase Vertex",
            "Erase Double Cut",
            "Iterate",
            "Deiterate",
        ]:
            btn = QPushButton(rule_name)
            btn.setEnabled(False)  # Will be enabled based on context
            btn.clicked.connect(
                lambda checked, name=rule_name: self._apply_transformation(name)
            )
            self.transform_buttons[rule_name] = btn
            transform_layout.addWidget(btn)

        layout.addWidget(transform_group)

        # Practice mode controls
        practice_group = QGroupBox("Practice Mode")
        practice_layout = QVBoxLayout(practice_group)

        self.practice_mode = QCheckBox("Enable Practice Mode")
        self.practice_mode.setChecked(True)
        practice_layout.addWidget(self.practice_mode)

        self.validation_label = QLabel("Validation: Ready")
        practice_layout.addWidget(self.validation_label)

        layout.addWidget(practice_group)

        # History panel
        history_group = QGroupBox("Transformation History")
        history_layout = QVBoxLayout(history_group)

        self.history_text = QTextEdit()
        self.history_text.setMaximumHeight(200)
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)

        # History controls
        history_controls = QHBoxLayout()
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self._undo_transformation)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_all)

        history_controls.addWidget(self.undo_btn)
        history_controls.addWidget(self.clear_btn)
        history_layout.addLayout(history_controls)

        layout.addWidget(history_group)

        # Stretch to fill remaining space
        layout.addStretch()

        return panel

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Sheet", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._initialize_empty_sheet)
        file_menu.addAction(new_action)

        file_menu.addSeparator()

        save_action = QAction("Save EGI", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_egi)
        file_menu.addAction(save_action)

        load_action = QAction("Load EGI", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_egi)
        file_menu.addAction(load_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self._undo_transformation)
        edit_menu.addAction(undo_action)

    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = self.addToolBar("Main")

        new_action = QAction("New", self)
        new_action.triggered.connect(self._initialize_empty_sheet)
        toolbar.addAction(new_action)

        toolbar.addSeparator()

        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_egi)
        toolbar.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.triggered.connect(self._load_egi)
        toolbar.addAction(load_action)

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Start with empty sheet")

    def _connect_signals(self):
        """Connect internal signals."""
        self.graph_changed.connect(self._on_graph_changed)
        self.practice_mode.toggled.connect(self._on_practice_mode_changed)

    def _initialize_empty_sheet(self):
        """Initialize with empty sheet of assertion."""
        from frozendict import frozendict

        # Create empty EGI following Dau's 6+1 component definition
        self.current_egi = RelationalGraphWithCuts(
            V=frozenset(),  # Empty set of vertices
            E=frozenset(),  # Empty set of edges
            nu=frozendict(),  # Empty ν mapping
            sheet="sheet_of_assertion",  # Sheet of assertion identifier
            Cut=frozenset(),  # Empty set of cuts
            area=frozendict(
                {"sheet_of_assertion": frozenset()}
            ),  # Sheet contains nothing initially
            rel=frozendict(),  # Empty relation mapping
        )

        self.transformation_history = [self.current_egi]
        self._update_display()
        self._update_available_transformations()
        self._add_history_entry("Initialized empty sheet")
        self.status_bar.showMessage("Empty sheet ready for composition")

    def _update_display(self):
        """Update the diagram display."""
        if self.current_egi is None:
            return

        # Clear scene
        self.diagram_scene.clear()

        # Render current EGI
        self.renderer.render_egi_to_scene(self.current_egi, self.diagram_scene)

        # Fit view
        self.diagram_view.fitInView(
            self.diagram_scene.itemsBoundingRect(), Qt.KeepAspectRatio
        )

    def _update_available_transformations(self):
        """Update which transformations are available based on current context."""
        if self.current_egi is None:
            return

        # For empty sheet, only allow vertex insertion and double cut insertion
        is_empty = len(self.current_egi.V) == 0 and len(self.current_egi.Cut) == 0

        if is_empty:
            self.transform_buttons["Insert Vertex"].setEnabled(True)
            self.transform_buttons["Insert Double Cut"].setEnabled(True)
            self.transform_buttons["Erase Vertex"].setEnabled(False)
            self.transform_buttons["Erase Double Cut"].setEnabled(False)
            self.transform_buttons["Iterate"].setEnabled(False)
            self.transform_buttons["Deiterate"].setEnabled(False)
        else:
            # Enable based on current graph content
            self.transform_buttons["Insert Vertex"].setEnabled(True)
            self.transform_buttons["Insert Double Cut"].setEnabled(True)
            self.transform_buttons["Erase Vertex"].setEnabled(
                len(self.current_egi.V) > 0
            )
            self.transform_buttons["Erase Double Cut"].setEnabled(
                len(self.current_egi.Cut) > 0
            )
            self.transform_buttons["Iterate"].setEnabled(len(self.current_egi.V) > 0)
            self.transform_buttons["Deiterate"].setEnabled(len(self.current_egi.V) > 0)

    def _apply_transformation(self, rule_name: str):
        """Apply a transformation rule."""
        if self.current_egi is None:
            return

        # Create new EGI based on transformation
        new_egi = self._execute_transformation(rule_name)

        if new_egi is not None:
            self.current_egi = new_egi
            self.transformation_history.append(new_egi)
            self._update_display()
            self._update_available_transformations()
            self._add_history_entry(f"Applied: {rule_name}")
            self.undo_btn.setEnabled(len(self.transformation_history) > 1)
            self.graph_changed.emit(new_egi)

    def _execute_transformation(
        self, rule_name: str
    ) -> Optional[RelationalGraphWithCuts]:
        """Execute a specific transformation rule."""
        # Simplified transformation execution for demo
        # In full implementation, this would use formal_transformation_rules

        new_egi = RelationalGraphWithCuts()
        new_egi.vertices = self.current_egi.vertices.copy()
        new_egi.edges = self.current_egi.edges.copy()
        new_egi.cuts = self.current_egi.cuts.copy()

        if rule_name == "Insert Vertex":
            # Add a simple vertex
            from egi_core_dau import Vertex

            vertex_id = f"v{len(new_egi.vertices) + 1}"
            new_vertex = Vertex(id=vertex_id, label="concept")
            new_egi.vertices[vertex_id] = new_vertex

        elif rule_name == "Insert Double Cut":
            # Add nested cuts
            from egi_core_dau import Cut

            outer_cut_id = f"c{len(new_egi.cuts) + 1}"
            inner_cut_id = f"c{len(new_egi.cuts) + 2}"

            outer_cut = Cut(
                id=outer_cut_id, vertices=set(), edges=set(), cuts={inner_cut_id}
            )
            inner_cut = Cut(id=inner_cut_id, vertices=set(), edges=set(), cuts=set())

            new_egi.cuts[outer_cut_id] = outer_cut
            new_egi.cuts[inner_cut_id] = inner_cut

        return new_egi

    def _undo_transformation(self):
        """Undo the last transformation."""
        if len(self.transformation_history) > 1:
            self.transformation_history.pop()
            self.current_egi = self.transformation_history[-1]
            self._update_display()
            self._update_available_transformations()
            self._add_history_entry("Undid last transformation")
            self.undo_btn.setEnabled(len(self.transformation_history) > 1)
            self.graph_changed.emit(self.current_egi)

    def _clear_all(self):
        """Clear all and start fresh."""
        self._initialize_empty_sheet()

    def _add_history_entry(self, entry: str):
        """Add an entry to the history display."""
        self.history_text.append(entry)

    def _on_graph_changed(self, egi: RelationalGraphWithCuts):
        """Handle graph change events."""
        vertex_count = len(egi.vertices)
        edge_count = len(egi.edges)
        cut_count = len(egi.cuts)
        self.status_bar.showMessage(
            f"Graph: {vertex_count} vertices, {edge_count} edges, {cut_count} cuts"
        )

    def _on_practice_mode_changed(self, enabled: bool):
        """Handle practice mode toggle."""
        if enabled:
            self.validation_label.setText("Validation: Enabled")
        else:
            self.validation_label.setText("Validation: Disabled")

    def _save_egi(self):
        """Save current EGI to file."""
        # Placeholder for save functionality
        self.status_bar.showMessage("Save functionality not yet implemented")

    def _load_egi(self):
        """Load EGI from file."""
        # Placeholder for load functionality
        self.status_bar.showMessage("Load functionality not yet implemented")


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = ErgasterionEditor()
    editor.show()
    sys.exit(app.exec())
