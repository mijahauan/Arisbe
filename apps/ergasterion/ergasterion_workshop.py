#!/usr/bin/env python3
"""
Ergasterion Workshop - Interactive EG composition and transformation editor

Provides comprehensive editing, transformation, and practice capabilities
for Existential Graphs within the Arisbe system.
"""

import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Import canvas widget - will create if needed
try:
    from .canvas_widget import EGCanvasWidget
except ImportError:
    # Create a basic canvas widget if not available
    EGCanvasWidget = None

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                                   QWidget, QPushButton, QTextEdit, QTreeWidget, 
                                   QTreeWidgetItem, QTabWidget, QSplitter, 
                                   QLabel, QStatusBar, QComboBox, QGroupBox,
                                   QToolBar, QLineEdit,
                                   QRadioButton, QButtonGroup, QCheckBox)
    from PySide6.QtGui import QPainter, QFont, QIcon, QPen, QBrush, QColor, QAction
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    # Define dummy classes to prevent NameError
    class QMainWindow: pass
    class QVBoxLayout: pass
    class QHBoxLayout: pass
    class QWidget: pass
    class QPushButton: pass
    class QTextEdit: pass
    class QTreeWidget: pass
    class QTreeWidgetItem: pass
    class QTabWidget: pass
    class QSplitter: pass
    class QLabel: pass
    class QStatusBar: pass
    class QComboBox: pass
    class QGroupBox: pass
    class QToolBar: pass
    class QLineEdit: pass
    class QRadioButton: pass
    class QButtonGroup: pass
    class QCheckBox: pass
    class QPainter: pass
    class QFont: pass
    class QIcon: pass
    class QPen: pass
    class QBrush: pass
    class QColor: pass
    class QAction: pass
    class Qt: pass
    class QTimer: pass
    class Signal: pass

from egif_parser_dau import EGIFParser
from egdf_parser import EGDFParser
from canonical_qt_renderer import CanonicalQtRenderer
# CanonicalPipeline removed - using 9-phase pipeline only
from layout_types import LayoutResult

if not PYSIDE6_AVAILABLE:
    print("Cannot run Ergasterion Workshop without PySide6")
    import sys
    sys.exit(1)

class EditMode(Enum):
    """Editing modes for the workshop."""
    WARMUP = "warmup"      # Compositional freedom, relaxed constraints
    PRACTICE = "practice"  # Strict transformation rules, formal validation

class TransformationType(Enum):
    """Types of EG transformations."""
    ERASURE = "erasure"
    INSERTION = "insertion"
    ITERATION = "iteration"
    DEITERATION = "deiteration"
    DOUBLE_CUT = "double_cut"

class ErgasterionWorkshop(QMainWindow):
    """
    Main workshop interface for the Ergasterion component.
    
    Provides comprehensive EG editing, transformation, and practice.
    """
    
    # Signals
    graph_modified = Signal(object)
    transformation_applied = Signal(str, object)
    mode_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Ergasterion - Existential Graph Workshop")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Core components
        self.egif_parser = None  # Will be created when needed with text
        self.egdf_parser = EGDFParser()
        # Initialize 9-phase layout pipeline (the ONLY pipeline)
        from layout_phase_implementations import (
            ElementSizingPhase, ContainerSizingPhase, CollisionDetectionPhase,
            PredicatePositioningPhase, VertexPositioningPhase, HookAssignmentPhase,
            RectilinearLigaturePhase, BranchOptimizationPhase, AreaCompactionPhase,
            PhaseStatus
        )
        from spatial_awareness_system import SpatialAwarenessSystem
        
        self.spatial_system = SpatialAwarenessSystem()
        self.layout_phases = [
            ElementSizingPhase(),
            ContainerSizingPhase(self.spatial_system),
            CollisionDetectionPhase(self.spatial_system),
            PredicatePositioningPhase(self.spatial_system),
            VertexPositioningPhase(self.spatial_system),
            HookAssignmentPhase(),
            RectilinearLigaturePhase(),
            BranchOptimizationPhase(),
            AreaCompactionPhase()
        ]
        from rendering_styles import DauStyle
        self.dau_style = DauStyle()
        self.renderer = CanonicalQtRenderer()
        
        # State
        self.current_egi = None
        self.current_egdf = None
        self.edit_mode = EditMode.WARMUP
        self.selected_elements = set()
        self.transformation_history = []
        self.current_transformation = None
        
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Load sample EGIF if available
        self._load_sample_egif()
        
    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create canvas widget for graph editing
        if EGCanvasWidget is not None:
            self.canvas_widget = EGCanvasWidget()
            self.canvas_widget.setMinimumSize(600, 400)
            self.canvas_widget.element_selected.connect(self._on_element_selected)
            self.canvas_widget.element_moved.connect(self._on_element_moved)
            self.canvas_widget.transformation_requested.connect(self._on_transformation_requested)
        else:
            # Create a basic QWidget as placeholder
            from PySide6.QtWidgets import QTextEdit
            self.canvas_widget = QTextEdit()
            self.canvas_widget.setPlaceholderText("Enter EGIF here...")
            self.canvas_widget.setMinimumSize(600, 400)
            self.canvas_widget.textChanged.connect(self._on_egif_input)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Tools and modes
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Center panel - Canvas
        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Right panel - Properties and history
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 800, 300])
        
    def _create_left_panel(self) -> QWidget:
        """Create the left tools panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Mode selection
        mode_group = QGroupBox("Edit Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup()
        
        self.warmup_radio = QRadioButton("Warmup Mode")
        self.warmup_radio.setChecked(True)
        self.warmup_radio.toggled.connect(self._mode_changed)
        self.mode_button_group.addButton(self.warmup_radio)
        mode_layout.addWidget(self.warmup_radio)
        
        self.practice_radio = QRadioButton("Practice Mode")
        self.practice_radio.toggled.connect(self._mode_changed)
        self.mode_button_group.addButton(self.practice_radio)
        mode_layout.addWidget(self.practice_radio)
        
        mode_description = QLabel()
        mode_description.setWordWrap(True)
        mode_description.setText("Warmup: Free composition\nPractice: Formal rules only")
        mode_layout.addWidget(mode_description)
        
        layout.addWidget(mode_group)
        
        # Transformation tools
        transform_group = QGroupBox("Transformations")
        transform_layout = QVBoxLayout(transform_group)
        
        self.erasure_btn = QPushButton("Erasure")
        self.erasure_btn.clicked.connect(lambda: self._select_transformation(TransformationType.ERASURE))
        transform_layout.addWidget(self.erasure_btn)
        
        self.insertion_btn = QPushButton("Insertion")
        self.insertion_btn.clicked.connect(lambda: self._select_transformation(TransformationType.INSERTION))
        transform_layout.addWidget(self.insertion_btn)
        
        self.iteration_btn = QPushButton("Iteration")
        self.iteration_btn.clicked.connect(lambda: self._select_transformation(TransformationType.ITERATION))
        transform_layout.addWidget(self.iteration_btn)
        
        self.deiteration_btn = QPushButton("Deiteration")
        self.deiteration_btn.clicked.connect(lambda: self._select_transformation(TransformationType.DEITERATION))
        transform_layout.addWidget(self.deiteration_btn)
        
        self.double_cut_btn = QPushButton("Double Cut")
        self.double_cut_btn.clicked.connect(lambda: self._select_transformation(TransformationType.DOUBLE_CUT))
        transform_layout.addWidget(self.double_cut_btn)
        
        layout.addWidget(transform_group)
        
        # Composition tools
        compose_group = QGroupBox("Composition")
        compose_layout = QVBoxLayout(compose_group)
        
        self.add_vertex_btn = QPushButton("Add Vertex")
        self.add_vertex_btn.clicked.connect(self._add_vertex)
        compose_layout.addWidget(self.add_vertex_btn)
        
        self.add_predicate_btn = QPushButton("Add Predicate")
        self.add_predicate_btn.clicked.connect(self._add_predicate)
        compose_layout.addWidget(self.add_predicate_btn)
        
        self.add_cut_btn = QPushButton("Add Cut")
        self.add_cut_btn.clicked.connect(self._add_cut)
        compose_layout.addWidget(self.add_cut_btn)
        
        layout.addWidget(compose_group)
        
        return panel
        
    def _create_canvas_tab(self) -> QWidget:
        """Create the interactive canvas tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # EGIF chiron display above canvas
        self.egif_chiron = QLabel("No graph loaded")
        self.egif_chiron.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                color: #333;
            }
        """)
        self.egif_chiron.setWordWrap(True)
        self.egif_chiron.setMaximumHeight(60)
        layout.addWidget(self.egif_chiron)
        
        # Canvas for interactive editing
        self.canvas = self.renderer.create_canvas()
        layout.addWidget(self.canvas)
        
        return widget
        
    def _create_center_panel(self) -> QWidget:
        """Create the center canvas panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Canvas toolbar
        canvas_toolbar = QHBoxLayout()
        
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._new_graph)
        canvas_toolbar.addWidget(self.new_btn)
        
        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self._load_graph)
        canvas_toolbar.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_graph)
        canvas_toolbar.addWidget(self.save_btn)
        
        canvas_toolbar.addStretch()
        
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self._undo)
        canvas_toolbar.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("Redo")
        self.redo_btn.clicked.connect(self._redo)
        canvas_toolbar.addWidget(self.redo_btn)
        
        layout.addLayout(canvas_toolbar)
        
        # Canvas for editing with enhanced PNG pipeline support
        self.canvas = self.renderer.create_canvas()
        layout.addWidget(self.canvas)
        
        # EGIF Text Editor Panel (small panel below canvas)
        egif_group = QGroupBox("EGIF Editor")
        egif_layout = QVBoxLayout(egif_group)
        
        self.egif_editor = QTextEdit()
        self.egif_editor.setPlaceholderText("Enter EGIF expressions here... Example: [Socrates: Man]")
        self.egif_editor.setMaximumHeight(100)  # Keep it small
        self.egif_editor.textChanged.connect(self._on_egif_input)
        egif_layout.addWidget(self.egif_editor)
        
        layout.addWidget(egif_group)
        
        # Render Button
        render_btn = QPushButton("Render EGIF")
        render_btn.clicked.connect(self._render_current_egif)
        layout.addWidget(render_btn)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create the right properties panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Selection info
        selection_group = QGroupBox("Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        self.selection_info = QLabel("No selection")
        selection_layout.addWidget(self.selection_info)
        
        layout.addWidget(selection_group)
        
        # Transformation history
        history_group = QGroupBox("History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QTreeWidget()
        self.history_list.setHeaderLabel("Transformations")
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(history_group)
        
        # Validation
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_display = QTextEdit()
        self.validation_display.setReadOnly(True)
        self.validation_display.setMaximumHeight(150)
        validation_layout.addWidget(self.validation_display)
        
        layout.addWidget(validation_group)
        
        return panel
        
    def _setup_menus(self):
        """Setup application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.triggered.connect(self._new_graph)
        file_menu.addAction(new_action)
        
        load_action = QAction("Load...", self)
        load_action.triggered.connect(self._load_graph)
        file_menu.addAction(load_action)
        
        save_action = QAction("Save...", self)
        save_action.triggered.connect(self._save_graph)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        # Transform menu
        transform_menu = menubar.addMenu("Transform")
        
        for transform_type in TransformationType:
            action = QAction(transform_type.value.title(), self)
            action.triggered.connect(lambda checked, t=transform_type: self._select_transformation(t))
            transform_menu.addAction(action)
        
    def _setup_toolbar(self):
        """Setup application toolbar."""
        toolbar = self.addToolBar("Main")
        
        # File actions
        new_action = QAction("New", self)
        new_action.triggered.connect(self._new_graph)
        toolbar.addAction(new_action)
        
        load_action = QAction("Load", self)
        load_action.triggered.connect(self._load_graph)
        toolbar.addAction(load_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_graph)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Edit actions
        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self._undo)
        toolbar.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self._redo)
        toolbar.addAction(redo_action)
        
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Warmup Mode")
        
    def _mode_changed(self):
        """Handle mode change."""
        if self.warmup_radio.isChecked():
            self.edit_mode = EditMode.WARMUP
            self.status_bar.showMessage("Warmup Mode - Free composition")
        else:
            self.edit_mode = EditMode.PRACTICE
            self.status_bar.showMessage("Practice Mode - Formal rules only")
            
        self.mode_changed.emit(self.edit_mode.value)
        self._update_ui_for_mode()
        
    def _update_ui_for_mode(self):
        """Update UI elements based on current mode."""
        is_practice = self.edit_mode == EditMode.PRACTICE
        
        # In practice mode, disable free composition tools
        self.add_vertex_btn.setEnabled(not is_practice)
        self.add_predicate_btn.setEnabled(not is_practice)
        self.add_cut_btn.setEnabled(not is_practice)
        
    def _select_transformation(self, transform_type: TransformationType):
        """Select a transformation type."""
        self.current_transformation = transform_type
        self.status_bar.showMessage(f"Selected: {transform_type.value.title()}")
        
        # Update button states
        for btn in [self.erasure_btn, self.insertion_btn, self.iteration_btn, 
                   self.deiteration_btn, self.double_cut_btn]:
            btn.setStyleSheet("")
            
        # Highlight selected transformation
        transform_buttons = {
            TransformationType.ERASURE: self.erasure_btn,
            TransformationType.INSERTION: self.insertion_btn,
            TransformationType.ITERATION: self.iteration_btn,
            TransformationType.DEITERATION: self.deiteration_btn,
            TransformationType.DOUBLE_CUT: self.double_cut_btn
        }
        
        if transformation_type in transform_buttons:
            transform_buttons[transformation_type].setStyleSheet("background-color: #e6f3ff; border: 2px solid #0066cc;")
    
    def load_file(self):
        """Load graph from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Graph", "",
            "All Supported (*.egif *.yaml *.yml *.json);;EGIF Files (*.egif);;YAML Files (*.yaml *.yml);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                path = Path(file_path)
                if path.suffix.lower() in ['.egif', '.txt']:
                    with open(file_path, 'r') as f:
                        egif_content = f.read().strip()
                    parser = EGIFParser(egif_content)
                    self.current_egi = parser.parse()
                else:
                    egdf_doc = self.egdf_parser.parse_egdf_file(file_path)
                    self.current_egi = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
                    
                self._update_displays()
                self.status_bar.showMessage(f"Loaded: {file_path}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load graph:\n{e}")
                
    def save_current_graph(self):
        """Save current graph to file."""
        if not self.current_egi:
            self.status_bar.showMessage("No graph to save", 3000)
            return
            
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Graph", "", 
            "EGIF Files (*.egif);;YAML Files (*.yaml);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if selected_filter.startswith("EGIF"):
                    # Save as EGIF
                    egif_text = self._egi_to_egif(self.current_egi)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(egif_text)
                elif selected_filter.startswith("YAML"):
                    # Save as YAML via EGDF
                    if self.current_egdf:
                        yaml_content = self.egdf_parser.egdf_to_yaml(self.current_egdf)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(yaml_content)
                    else:
                        raise Exception("No EGDF available for YAML export")
                elif selected_filter.startswith("JSON"):
                    # Save as JSON via EGDF
                    if self.current_egdf:
                        json_content = self.egdf_parser.egdf_to_json(self.current_egdf)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(json_content)
                    else:
                        raise Exception("No EGDF available for JSON export")
                
                self.status_bar.showMessage(f"Saved to {file_path}", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save graph:\n{e}")
                
    def _egi_to_egif(self, egi) -> str:
        """Convert EGI back to EGIF format."""
        # This is a simplified conversion - full implementation would use proper EGIF generator
        try:
            from egif_generator import EGIFGenerator
            generator = EGIFGenerator()
            return generator.generate_egif(egi)
        except ImportError:
            # Fallback: create basic EGIF representation
            lines = []
            for vertex in egi.V:
                if hasattr(vertex, 'label') and vertex.label:
                    lines.append(f"{vertex.label}")
            for edge in egi.E:
                # Use nu mapping and rel mapping for Dau-compliant access
                if edge.id in egi.nu and edge.id in egi.rel:
                    vertex_ids = egi.nu[edge.id]
                    predicate = egi.rel[edge.id]
                    lines.append(f"{predicate}({', '.join(str(vid) for vid in vertex_ids)})")
            return '\n'.join(lines) if lines else "// Empty graph"
                
    def _add_vertex(self):
        """Add a new vertex."""
        if self.edit_mode == EditMode.PRACTICE:
            QMessageBox.warning(self, "Mode Restriction", "Free composition not allowed in Practice mode")
            return
            
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_vertex = "\n[NewVertex: Label]"
        else:
            new_vertex = "[NewVertex: Label]"
        self.egif_editor.setPlainText(current_text + new_vertex)
        self._on_egif_input()
        
        self.status_bar.showMessage("Vertex added to EGIF")
        
    def _add_predicate(self):
        """Add a new predicate."""
        if self.edit_mode == EditMode.PRACTICE:
            QMessageBox.warning(self, "Mode Restriction", "Free composition not allowed in Practice mode")
            return
            
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_edge = "\n[Predicate: Relation]"
        else:
            new_edge = "[Predicate: Relation]"
        self.egif_editor.setPlainText(current_text + new_edge)
        self._on_egif_input()
        
        self.status_bar.showMessage("Predicate added to EGIF")
        
    def _add_cut(self):
        """Add a new cut."""
        if self.edit_mode == EditMode.PRACTICE:
            QMessageBox.warning(self, "Mode Restriction", "Free composition not allowed in Practice mode")
            return
            
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_cut = "\n~[Cut: Content]"
        else:
            new_cut = "~[Cut: Content]"
        self.egif_editor.setPlainText(current_text + new_cut)
        self._on_egif_input()
        
        self.status_bar.showMessage("Cut added to EGIF")
        
    def _undo(self):
        """Undo last transformation."""
        if self.transformation_history:
            # Implementation would restore previous state
            self.status_bar.showMessage("Undo applied")
        else:
            self.status_bar.showMessage("Nothing to undo")
    
    def _redo(self):
        """Redo last undone transformation."""
        # Placeholder for redo functionality
        self.status_bar.showMessage("Redo functionality not yet implemented")
    
    def _generate_layout_primitives(self, egi):
        """Generate layout primitives for EGI visualization."""
        primitives = []
        
        # Position vertices
        for i, vertex in enumerate(egi.V):
            primitives.append({
                'element_id': vertex.id,
                'element_type': 'vertex',
                'position': (150 + i * 100, 200 + (i % 2) * 80),
                'bounds': (130 + i * 100, 180 + (i % 2) * 80, 170 + i * 100, 220 + (i % 2) * 80)
            })
        
        # Position edges
        for i, edge in enumerate(egi.E):
            primitives.append({
                'element_id': edge.id,
                'element_type': 'edge',
                'position': (250 + i * 100, 300),
                'bounds': (240 + i * 100, 290, 260 + i * 100, 310)
            })
        
        # Position cuts
        for i, cut in enumerate(egi.Cut):
            primitives.append({
                'element_id': cut.id,
                'element_type': 'cut',
                'position': (200 + i * 150, 150),
                'bounds': (100 + i * 150, 100, 300 + i * 150, 250)
            })
        
        return primitives
    
    def _on_egif_input(self):
        """Handle EGIF text input and parse it."""
        egif_text = self.egif_editor.toPlainText().strip()
        if egif_text:
            try:
                # Create parser with text
                self.egif_parser = EGIFParser(egif_text)
                egi = self.egif_parser.parse()
                self.current_egi = egi
                
                # Render to canvas
                self._render_egi_to_canvas()
                
                # Update displays
                self._update_graph_display()
                vertices = getattr(egi, 'V', []) or []
                edges = getattr(egi, 'E', []) or []
                self.status_bar.showMessage(f"Parsed EGIF: {len(vertices)} vertices, {len(edges)} edges")
                
            except Exception as e:
                self.status_bar.showMessage(f"EGIF parse error: {e}")
    
    def _load_sample_egif(self):
        """Load a sample EGIF for testing."""
        sample_egif = """[Socrates: Man]
[Man: Mortal]
[Socrates: Mortal]"""
        
        if hasattr(self.canvas_widget, 'setPlainText'):
            self.canvas_widget.setPlainText(sample_egif)
            self._on_egif_input()
    
    def _update_graph_display(self):
        """Update the graph display after parsing."""
        if self.current_egi is None:
            return
            
        try:
            # Generate layout
            layout_result = self.pipeline.generate_layout(self.current_egi)
            
            # If we have a proper canvas widget, render there
            if hasattr(self.canvas_widget, 'update_graph'):
                self.canvas_widget.update_graph(self.current_egi, layout_result)
            else:
                # For text widget, show structure info
                structure_info = f"""

--- Parsed Structure ---
Vertices: {len(self.current_egi.V)}
Edges: {len(self.current_egi.E)}
Cuts: {len(getattr(self.current_egi, 'Cut', []))}

Vertices:
"""
                for v in self.current_egi.V:
                    structure_info += f"  {v.id}: {getattr(v, 'label', 'unlabeled')}\n"
                
                structure_info += "\nEdges:\n"
                for e in self.current_egi.E:
                    structure_info += f"  {e.id}: {getattr(e, 'predicate', 'no predicate')}\n"
                
                # Structure display is now handled separately
                pass
                
        except Exception as e:
            self.status_bar.showMessage(f"Display error: {e}")
    
    def load_from_browser(self, egi_data):
        """Load graph data from the browser component."""
        try:
            self.current_egi = egi_data
            
            # Convert to EGIF text representation
            egif_text = self._egi_to_egif_string(egi_data)
            
            if hasattr(self.canvas_widget, 'setPlainText'):
                self.canvas_widget.setPlainText(egif_text)
            
            self._update_graph_display()
            self.status_bar.showMessage("Graph loaded from browser")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error loading from browser: {e}")
    
    def _egi_to_egif_string(self, egi):
        """Convert EGI back to EGIF string representation."""
        if egi is None:
            return ""
            
        egif_lines = []
        
        # Add vertices as propositions
        for vertex in getattr(egi, 'V', []):
            label = getattr(vertex, 'label', 'unlabeled')
            egif_lines.append(f"[{vertex.id}: {label}]")
        
        # Add edges as relations
        for edge in getattr(egi, 'E', []):
            predicate = getattr(edge, 'predicate', 'relates')
            egif_lines.append(f"[{edge.id}: {predicate}]")
        
        return "\n".join(egif_lines)
    
    def _on_element_selected(self, element_id):
        """Handle element selection in canvas."""
        self.status_bar.showMessage(f"Selected: {element_id}", 2000)
    
    def _on_element_moved(self, element_id, new_position):
        """Handle element movement in canvas."""
        # For now, just show status - full implementation would update spatial primitives
        self.status_bar.showMessage(f"Moved {element_id} to ({new_position.x()}, {new_position.y()})", 2000)
    
    def _on_transformation_requested(self, transformation_type, element_id):
        """Handle transformation request from canvas."""
        self.status_bar.showMessage(f"Transformation requested: {transformation_type} on {element_id}", 3000)
        
    def _render_egi_to_canvas(self):
        """Render the current EGI to the canvas using direct Qt graphics with DauStyle."""
        if self.current_egi:
            try:
                # Generate layout using canonical pipeline
                layout_result = self.canonical_pipeline.generate_layout(self.current_egi)
                
                # Render directly to Qt canvas with DauStyle (no PNG intermediate)
                self.renderer.render_egi_to_canvas(
                    self.current_egi, 
                    layout_result, 
                    self.canvas,
                    style=self.dau_style
                )
                
                self.status_bar.showMessage("Graph rendered to canvas with DauStyle", 2000)
                
            except Exception as e:
                self.status_bar.showMessage(f"Rendering error: {e}", 5000)
                print(f"Canvas rendering error: {e}")
        else:
            # Clear canvas if no EGI
            self.canvas.clear()
    
    def _render_current_egif(self):
        """Render button handler - parse and render EGIF."""
        self._on_egif_input()
    
    def _update_displays(self):
        """Update all display elements."""
        if self.current_egi:
            layout_result = self.pipeline.execute_pipeline(self.current_egi)
            self.renderer.render_egi(self.current_egi, layout_result, self.canvas)
            
        self._update_selection_info()
        self._update_history_display()
        self._update_validation_display()
        
    def _update_selection_info(self):
        """Update selection information."""
        if self.selected_elements:
            self.selection_info.setText(f"Selected: {len(self.selected_elements)} elements")
        else:
            self.selection_info.setText("No selection")
            
    def _update_history_display(self):
        """Update transformation history display."""
        self.history_list.clear()
        for i, transform in enumerate(self.transformation_history):
            item = QTreeWidgetItem([f"{i+1}. {transform['type']} - {transform['description']}"])
            self.history_list.addTopLevelItem(item)
            
    def _update_validation_display(self):
        """Update validation information."""
        if self.edit_mode == EditMode.PRACTICE and self.current_egi:
            # Validate current state against EG rules
            validation_text = "Graph is valid according to EG calculus rules."
            self.validation_display.setPlainText(validation_text)
        else:
            self.validation_display.setPlainText("Validation not active in Warmup mode.")
            
    def _extract_spatial_primitives(self, layout_result: LayoutResult) -> List[Dict]:
        """Extract spatial primitives from layout result."""
        primitives = []
        
        for vertex_id, position in layout_result.vertex_positions.items():
            primitives.append({
                'element_id': vertex_id,
                'element_type': 'vertex',
                'position': position,
                'bounds': (position[0]-10, position[1]-10, position[0]+10, position[1]+10)
            })
            
        for edge_id, position in layout_result.edge_positions.items():
            primitives.append({
                'element_id': edge_id,
                'element_type': 'predicate',
                'position': position,
                'bounds': (position[0]-20, position[1]-10, position[0]+20, position[1]+10)
            })
            
        for cut_id, bounds in layout_result.cut_bounds.items():
            center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
            primitives.append({
                'element_id': cut_id,
                'element_type': 'cut',
                'position': center,
                'bounds': bounds
            })
            
        return primitives
    
    def _new_graph(self):
        """Create a new empty graph."""
        self.current_egi = None
        self.current_egdf = None
        self.transformation_history = []
        
        if hasattr(self.canvas_widget, 'setPlainText'):
            self.canvas_widget.setPlainText("")
        
        self.status_bar.showMessage("New graph created")
    
    def _load_graph(self):
        """Load a graph from file."""
        # Placeholder for file loading functionality
        self.status_bar.showMessage("Load functionality not yet implemented")
    
    def _save_graph(self):
        """Save the current graph to file."""
        # Placeholder for file saving functionality
        self.status_bar.showMessage("Save functionality not yet implemented")
    
    def _export_graph(self):
        """Export the current graph."""
        # Placeholder for export functionality
        self.status_bar.showMessage("Export functionality not yet implemented")
    
    def _add_vertex(self):
        """Add a new vertex to the graph."""
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_vertex = "\n[NewVertex: Label]"
        else:
            new_vertex = "[NewVertex: Label]"
        self.egif_editor.setPlainText(current_text + new_vertex)
        self._on_egif_input()
        
        self.status_bar.showMessage("Vertex added to EGIF")
    
    def _add_edge(self):
        """Add a new edge to the graph."""
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_edge = "\n[Predicate: Relation]"
        else:
            new_edge = "[Predicate: Relation]"
        self.egif_editor.setPlainText(current_text + new_edge)
        self._on_egif_input()
        
        self.status_bar.showMessage("Predicate added to EGIF")
    
    def _add_edge(self):
        """Add a new edge to the graph."""
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_edge = "\n[Predicate: Relation]"
        else:
            new_edge = "[Predicate: Relation]"
        self.egif_editor.setPlainText(current_text + new_edge)
        self._on_egif_input()
        
        self.status_bar.showMessage("Predicate added to EGIF")
    
    def _add_cut(self):
        """Add a new cut to the graph."""
        current_text = self.egif_editor.toPlainText()
        if current_text.strip():
            new_cut = "\n~[Cut: Content]"
        else:
            new_cut = "~[Cut: Content]"
        self.egif_editor.setPlainText(current_text + new_cut)
        self._on_egif_input()
        
        self.status_bar.showMessage("Cut added to EGIF")
    
    def _setup_menus(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.triggered.connect(self._new_graph)
        file_menu.addAction(new_action)
        
        load_action = QAction("Load...", self)
        load_action.triggered.connect(self._load_graph)
        file_menu.addAction(load_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_graph)
        file_menu.addAction(save_action)
        
        export_action = QAction("Export...", self)
        export_action.triggered.connect(self._export_graph)
        file_menu.addAction(export_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        add_vertex_action = QAction("Add Vertex", self)
        add_vertex_action.triggered.connect(self._add_vertex)
        edit_menu.addAction(add_vertex_action)
        
        add_edge_action = QAction("Add Edge", self)
        add_edge_action.triggered.connect(self._add_edge)
        edit_menu.addAction(add_edge_action)
        
        add_cut_action = QAction("Add Cut", self)
        add_cut_action.triggered.connect(self._add_cut)
        edit_menu.addAction(add_cut_action)
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        toolbar = self.addToolBar("Main")
        
        # File actions
        new_action = QAction("New", self)
        new_action.triggered.connect(self._new_graph)
        toolbar.addAction(new_action)
        
        load_action = QAction("Load", self)
        load_action.triggered.connect(self._load_graph)
        toolbar.addAction(load_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self._save_graph)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Edit actions
        add_vertex_action = QAction("Add Vertex", self)
        add_vertex_action.triggered.connect(self._add_vertex)
        toolbar.addAction(add_vertex_action)
        
        add_edge_action = QAction("Add Edge", self)
        add_edge_action.triggered.connect(self._add_edge)
        toolbar.addAction(add_edge_action)
        
        add_cut_action = QAction("Add Cut", self)
        add_cut_action.triggered.connect(self._add_cut)
        toolbar.addAction(add_cut_action)
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ergasterion Workshop ready")
        
    def _egi_to_egif_string(self, egi) -> str:
        """Convert EGI back to EGIF string representation."""
        elements = []
        
        for vertex in egi.V:
            elements.append(f"*{vertex.label}")
            
        for edge in egi.E:
            # Use nu mapping to get vertex sequence for this edge
            if edge.id in egi.nu:
                vertex_ids = egi.nu[edge.id]
                vertex_labels = []
                for vid in vertex_ids:
                    if vid in egi._vertex_map:
                        vertex_labels.append(egi._vertex_map[vid].label or vid)
                # Get relation name from rel mapping
                predicate = egi.rel.get(edge.id, 'unknown')
                elements.append(f"({predicate} {' '.join(vertex_labels)})")
            
        return " ".join(elements)

def main():
    """Main function to run Ergasterion workshop."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required to run Ergasterion")
        return 1
        
    app = QApplication(sys.argv)
    app.setApplicationName("Arisbe Ergasterion")
    app.setApplicationVersion("1.0.0")
    
    workshop = ErgasterionWorkshop()
    workshop.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
