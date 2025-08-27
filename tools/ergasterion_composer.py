#!/usr/bin/env python3
"""
Ergasterion Composer/Editor - Enhanced drawing tool for constructing and editing EGI drawings.

This is the core Composer/Editor function of Ergasterion, Arisbe's workshop for Existential Graphs.
It provides a robust environment for:
- Composing EG diagrams with proper constraints
- Editing existing graphs with validation
- Practicing transformation rules
- Integrating with the corpus of examples

Key enhancements over the minimal drawing tool:
- Improved UI with mode indicators and status feedback
- Better corpus integration for loading examples
- Enhanced constraint validation and user guidance
- Preparation for transformation rule scaffolding
- Cleaner separation between composition and practice modes
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src directory to path for custom modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from drawing_editor_integration import integrate_drawing_editor
from practice_mode_integration import integrate_practice_mode


import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal, QObject
from PySide6.QtGui import QAction, QPen, QBrush, QColor, QKeySequence, QFont, QPixmap, QPainter
from PySide6.QtWidgets import (
    QApplication, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem,
    QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView,
    QInputDialog, QMainWindow, QMessageBox, QFileDialog, QToolBar,
    QDockWidget, QTabWidget, QTextEdit, QWidget, QMenu, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QComboBox, QSplitter, QListWidget,
    QListWidgetItem, QGroupBox, QCheckBox, QSpinBox, QSlider, QStatusBar,
    QFrame, QScrollArea
)


class WorkshopMode(Enum):
    """Ergasterion workshop modes."""
    COMPOSITION = "composition"  # Free-form creation and editing
    PRACTICE = "practice"       # Rule-based transformations with constraints


class InteractionMode(Enum):
    """Current interaction mode within the workshop."""
    SELECT = "select"
    ADD_CUT = "add_cut"
    ADD_VERTEX = "add_vertex"
    ADD_PREDICATE = "add_predicate"
    LIGATURE = "ligature"
    TRANSFORM = "transform"  # For practice mode transformations


# ---------- Enhanced Data Models ----------
@dataclass
class CutItem:
    """Enhanced cut item with additional metadata."""
    id: str
    rect: QRectF
    parent_id: Optional[str]
    gfx: QGraphicsRectItem
    label: Optional[str] = None  # Optional semantic label
    created_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.created_timestamp is None:
            self.created_timestamp = datetime.now().isoformat()


@dataclass
class VertexItem:
    """Enhanced vertex item with additional metadata."""
    id: str
    pos: QPointF
    area_id: str
    gfx: QGraphicsEllipseItem
    label: Optional[str] = None
    label_kind: Optional[str] = None  # "constant" | "variable" | "generic"
    gfx_label: Optional[QGraphicsTextItem] = None
    created_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.created_timestamp is None:
            self.created_timestamp = datetime.now().isoformat()


@dataclass
class PredicateItem:
    """Enhanced predicate item with additional metadata."""
    id: str
    name: str
    pos: QPointF
    area_id: str
    gfx_text: QGraphicsTextItem
    gfx_rect: QGraphicsRectItem
    arity: Optional[int] = None  # Expected number of arguments
    created_timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.created_timestamp is None:
            self.created_timestamp = datetime.now().isoformat()


@dataclass
class TransformationStep:
    """Record of a transformation applied to the graph."""
    step_id: str
    rule_name: str
    description: str
    timestamp: str
    before_state: Dict  # Serialized graph state before transformation
    after_state: Dict   # Serialized graph state after transformation
    is_valid: bool = True
    validation_notes: Optional[str] = None


@dataclass
class ErgasterionModel:
    """Enhanced model for Ergasterion workshop."""
    sheet_id: str = "S"
    cuts: Dict[str, CutItem] = field(default_factory=dict)
    vertices: Dict[str, VertexItem] = field(default_factory=dict)
    predicates: Dict[str, PredicateItem] = field(default_factory=dict)
    ligatures: Dict[str, List[str]] = field(default_factory=dict)
    predicate_outputs: Dict[str, str] = field(default_factory=dict)
    
    # Workshop metadata
    workshop_mode: WorkshopMode = WorkshopMode.COMPOSITION
    source_corpus_id: Optional[str] = None
    transformation_history: List[TransformationStep] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    
    def to_schema(self) -> Dict:
        """Convert to JSON schema compatible with drawing_to_egi_adapter."""
        return {
            "sheet_id": self.sheet_id,
            "cuts": [
                {
                    "id": c.id, 
                    "parent_id": c.parent_id,
                    "label": c.label,
                    "created_timestamp": c.created_timestamp
                } 
                for c in self.cuts.values()
            ],
            "vertices": [
                {
                    **{"id": v.id, "area_id": v.area_id},
                    **({"label": v.label} if v.label else {}),
                    **({"label_kind": v.label_kind} if v.label_kind else {}),
                    "created_timestamp": v.created_timestamp,
                }
                for v in self.vertices.values()
            ],
            "predicates": [
                {
                    "id": p.id, 
                    "name": p.name, 
                    "area_id": p.area_id,
                    "arity": p.arity,
                    "created_timestamp": p.created_timestamp
                } 
                for p in self.predicates.values()
            ],
            "ligatures": [
                {"edge_id": e, "vertex_ids": vids} for e, vids in self.ligatures.items()
            ],
            "predicate_outputs": self.predicate_outputs,
            "workshop_metadata": {
                "mode": self.workshop_mode.value,
                "source_corpus_id": self.source_corpus_id,
                "transformation_count": len(self.transformation_history),
                "has_validation_errors": len(self.validation_errors) > 0
            }
        }
    
    def add_transformation_step(self, rule_name: str, description: str, 
                              before_state: Dict, after_state: Dict) -> str:
        """Add a transformation step to the history."""
        step_id = f"transform_{len(self.transformation_history) + 1}"
        step = TransformationStep(
            step_id=step_id,
            rule_name=rule_name,
            description=description,
            timestamp=datetime.now().isoformat(),
            before_state=before_state,
            after_state=after_state
        )
        self.transformation_history.append(step)
        return step_id
    
    def validate_constraints(self) -> List[str]:
        """Validate EG constraints and return list of errors."""
        errors = []
        
        # Check cut nesting constraints
        for cut_id, cut in self.cuts.items():
            for other_id, other_cut in self.cuts.items():
                if cut_id != other_id:
                    # Check for partial overlaps (invalid)
                    if self._rects_partially_overlap(cut.rect, other_cut.rect):
                        errors.append(f"Cuts {cut_id} and {other_id} have invalid partial overlap")
        
        # Check vertex-area consistency
        for vertex_id, vertex in self.vertices.items():
            if vertex.area_id not in self.cuts and vertex.area_id != self.sheet_id:
                errors.append(f"Vertex {vertex_id} references non-existent area {vertex.area_id}")
        
        # Check predicate-area consistency
        for pred_id, pred in self.predicates.items():
            if pred.area_id not in self.cuts and pred.area_id != self.sheet_id:
                errors.append(f"Predicate {pred_id} references non-existent area {pred.area_id}")
        
        # Check ligature consistency
        for edge_id, vertex_ids in self.ligatures.items():
            if edge_id not in self.predicates:
                errors.append(f"Ligature references non-existent predicate {edge_id}")
            for vertex_id in vertex_ids:
                if vertex_id not in self.vertices:
                    errors.append(f"Ligature references non-existent vertex {vertex_id}")
        
        self.validation_errors = errors
        return errors
    
    def _rects_partially_overlap(self, rect1: QRectF, rect2: QRectF) -> bool:
        """Check if two rectangles have partial overlap (invalid for cuts)."""
        if not rect1.intersects(rect2):
            return False  # No overlap
        
        # Check if one contains the other (valid nesting)
        if rect1.contains(rect2) or rect2.contains(rect1):
            return False  # Valid nesting
        
        return True  # Partial overlap (invalid)


# ---------- Enhanced UI Components ----------
class WorkshopStatusWidget(QWidget):
    """Status widget showing current workshop mode and validation state."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Mode indicator
        self.mode_label = QLabel("Mode: Composition")
        self.mode_label.setStyleSheet("font-weight: bold; color: #2563eb;")
        layout.addWidget(self.mode_label)
        
        layout.addWidget(QLabel("|"))
        
        # Validation status
        self.validation_label = QLabel("✓ Valid")
        self.validation_label.setStyleSheet("color: #16a34a;")
        layout.addWidget(self.validation_label)
        
        layout.addWidget(QLabel("|"))
        
        # Element count
        self.count_label = QLabel("Elements: 0")
        layout.addWidget(self.count_label)
        
        layout.addStretch()
    
    def update_mode(self, mode: WorkshopMode):
        """Update the mode indicator."""
        mode_text = "Composition" if mode == WorkshopMode.COMPOSITION else "Practice"
        self.mode_label.setText(f"Mode: {mode_text}")
        
        if mode == WorkshopMode.COMPOSITION:
            self.mode_label.setStyleSheet("font-weight: bold; color: #2563eb;")
        else:
            self.mode_label.setStyleSheet("font-weight: bold; color: #dc2626;")
    
    def update_validation(self, is_valid: bool, error_count: int = 0):
        """Update the validation status."""
        if is_valid:
            self.validation_label.setText("✓ Valid")
            self.validation_label.setStyleSheet("color: #16a34a;")
        else:
            self.validation_label.setText(f"⚠ {error_count} Error{'s' if error_count != 1 else ''}")
            self.validation_label.setStyleSheet("color: #dc2626;")
    
    def update_counts(self, cuts: int, vertices: int, predicates: int):
        """Update element counts."""
        total = cuts + vertices + predicates
        self.count_label.setText(f"Elements: {total} (C:{cuts} V:{vertices} P:{predicates})")


class CorpusBrowserWidget(QWidget):
    """Widget for browsing and loading corpus examples."""
    
    corpus_selected = Signal(str, dict)  # corpus_id, metadata
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.corpus_items = {}  # id -> metadata
        self.setup_ui()
        self.load_corpus_index()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Corpus Browser")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header)
        
        # Search/filter controls
        filter_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Peirce", "Scholars", "Canonical", "Challenging"])
        self.category_combo.currentTextChanged.connect(self.filter_corpus)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_combo)
        layout.addLayout(filter_layout)
        
        # Corpus list
        self.corpus_list = QListWidget()
        self.corpus_list.itemDoubleClicked.connect(self.on_corpus_selected)
        layout.addWidget(self.corpus_list)
        
        # Load button
        load_btn = QPushButton("Load Selected")
        load_btn.clicked.connect(self.load_selected)
        layout.addWidget(load_btn)
    
    def load_corpus_index(self):
        """Load available corpus items."""
        # This would integrate with the actual corpus system
        # For now, add some sample items
        sample_items = [
            {
                "id": "peirce_man_mortal",
                "title": "Peirce: Man-Mortal Implication",
                "category": "Peirce",
                "description": "Classic example of implication",
                "egif": '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
            },
            {
                "id": "dau_ligature_example",
                "title": "Dau: Ligature Example",
                "category": "Scholars", 
                "description": "Demonstrates proper ligature usage",
                "egif": '*x (Human x) (Mortal x)'
            }
        ]
        
        for item in sample_items:
            self.corpus_items[item["id"]] = item
        
        self.filter_corpus()
    
    def filter_corpus(self):
        """Filter corpus list based on selected category."""
        self.corpus_list.clear()
        category = self.category_combo.currentText()
        
        for item_id, item in self.corpus_items.items():
            if category == "All" or item["category"] == category:
                list_item = QListWidgetItem(f"{item['title']}")
                list_item.setData(Qt.UserRole, item_id)
                list_item.setToolTip(item["description"])
                self.corpus_list.addItem(list_item)
    
    def on_corpus_selected(self, item: QListWidgetItem):
        """Handle corpus item double-click."""
        self.load_selected()
    
    def load_selected(self):
        """Load the selected corpus item."""
        current = self.corpus_list.currentItem()
        if current:
            item_id = current.data(Qt.UserRole)
            if item_id in self.corpus_items:
                self.corpus_selected.emit(item_id, self.corpus_items[item_id])


class TransformationPaletteWidget(QWidget):
    """Widget for transformation rules in practice mode."""
    
    transformation_requested = Signal(str, str)  # rule_name, description
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Transformation Rules")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header)
        
        # Rule categories
        self.create_rule_group("Basic Rules", [
            ("insertion", "Insertion", "Insert a graph into any context"),
            ("erasure", "Erasure", "Erase a graph from positive context"),
            ("iteration", "Iteration", "Copy within same context"),
            ("deiteration", "Deiteration", "Remove duplicate in same context")
        ], layout)
        
        self.create_rule_group("Cut Rules", [
            ("double_cut", "Double Cut", "Insert/remove double negation"),
            ("cut_insertion", "Cut Insertion", "Insert empty cut"),
            ("cut_erasure", "Cut Erasure", "Remove empty cut")
        ], layout)
        
        layout.addStretch()
    
    def create_rule_group(self, title: str, rules: List[Tuple[str, str, str]], layout: QVBoxLayout):
        """Create a group of transformation rule buttons."""
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        
        for rule_id, rule_name, description in rules:
            btn = QPushButton(rule_name)
            btn.setToolTip(description)
            btn.clicked.connect(lambda checked, r=rule_id, d=description: 
                              self.transformation_requested.emit(r, d))
            group_layout.addWidget(btn)
        
        layout.addWidget(group)


# ---------- Enhanced Main Editor ----------
class ErgasterionComposerEditor(QMainWindow):
    """Enhanced drawing editor serving as Ergasterion's Composer/Editor function."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ergasterion - Composer/Editor")
        self.resize(1400, 900)
        
        # Core components
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 1200, 800)
        self.view = QGraphicsView(self.scene)
        self.model = ErgasterionModel()
        
        # UI state
        self.interaction_mode = InteractionMode.SELECT
        self.workshop_mode = WorkshopMode.COMPOSITION
        
        # Visual elements
        self._ligature_lines: List[QGraphicsLineItem] = []
        self._ligature_drag_from_vid: Optional[str] = None
        self._ligature_drag_line: Optional[QGraphicsLineItem] = None
        self._interaction_active: bool = False
        
        # Drag state
        self._drag_start: Optional[QPointF] = None
        self._cut_preview_item: Optional[QGraphicsRectItem] = None
        
        self.setup_ui()
        self.setup_connections()
        self.update_ui_for_mode()
    
    def setup_ui(self):
        """Set up the enhanced user interface."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel for corpus and tools
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel for drawing
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # Right panel for properties and validation
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 700, 300])
        
        # Toolbar
        self.create_toolbar()
        
        # Status bar with workshop status
        self.status_widget = WorkshopStatusWidget()
        self.statusBar().addPermanentWidget(self.status_widget)
        
        # Install event filter for mouse interactions
        self.view.viewport().installEventFilter(self)
    
    def create_left_panel(self) -> QWidget:
        """Create the left panel with corpus browser and mode controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Mode selection
        mode_group = QGroupBox("Workshop Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.composition_radio = QCheckBox("Composition Mode")
        self.composition_radio.setChecked(True)
        self.composition_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.composition_radio)
        
        self.practice_radio = QCheckBox("Practice Mode")
        self.practice_radio.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.practice_radio)
        
        layout.addWidget(mode_group)
        
        # Corpus browser
        self.corpus_browser = CorpusBrowserWidget()
        self.corpus_browser.corpus_selected.connect(self.load_corpus_item)
        layout.addWidget(self.corpus_browser)
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """Create the center panel with the drawing canvas."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Canvas controls
        controls_layout = QHBoxLayout()
        
        # Interaction mode buttons
        self.select_btn = QPushButton("Select")
        self.select_btn.setCheckable(True)
        self.select_btn.setChecked(True)
        self.select_btn.clicked.connect(lambda: self.set_interaction_mode(InteractionMode.SELECT))
        controls_layout.addWidget(self.select_btn)
        
        self.add_cut_btn = QPushButton("Add Cut")
        self.add_cut_btn.setCheckable(True)
        self.add_cut_btn.clicked.connect(lambda: self.set_interaction_mode(InteractionMode.ADD_CUT))
        controls_layout.addWidget(self.add_cut_btn)
        
        self.add_vertex_btn = QPushButton("Add Vertex")
        self.add_vertex_btn.setCheckable(True)
        self.add_vertex_btn.clicked.connect(lambda: self.set_interaction_mode(InteractionMode.ADD_VERTEX))
        controls_layout.addWidget(self.add_vertex_btn)
        
        self.add_pred_btn = QPushButton("Add Predicate")
        self.add_pred_btn.setCheckable(True)
        self.add_pred_btn.clicked.connect(lambda: self.set_interaction_mode(InteractionMode.ADD_PREDICATE))
        controls_layout.addWidget(self.add_pred_btn)
        
        self.ligature_btn = QPushButton("Ligature")
        self.ligature_btn.setCheckable(True)
        self.ligature_btn.clicked.connect(lambda: self.set_interaction_mode(InteractionMode.LIGATURE))
        controls_layout.addWidget(self.ligature_btn)
        
        controls_layout.addStretch()
        
        # Zoom controls
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self.view.scale(0.8, 0.8))
        controls_layout.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self.view.scale(1.25, 1.25))
        controls_layout.addWidget(zoom_in_btn)
        
        layout.addLayout(controls_layout)
        
        # Drawing canvas
        self.view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.view)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel with transformation tools and validation."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Transformation palette (for practice mode)
        self.transformation_palette = TransformationPaletteWidget()
        self.transformation_palette.transformation_requested.connect(self.apply_transformation)
        layout.addWidget(self.transformation_palette)
        
        # Validation panel
        validation_group = QGroupBox("Validation")
        validation_layout = QVBoxLayout(validation_group)
        
        validate_btn = QPushButton("Validate Graph")
        validate_btn.clicked.connect(self.validate_graph)
        validation_layout.addWidget(validate_btn)
        
        self.validation_text = QTextEdit()
        self.validation_text.setMaximumHeight(150)
        self.validation_text.setReadOnly(True)
        validation_layout.addWidget(self.validation_text)
        
        layout.addWidget(validation_group)
        
        # Properties panel
        properties_group = QGroupBox("Properties")
        properties_layout = QVBoxLayout(properties_group)
        
        self.properties_text = QTextEdit()
        self.properties_text.setMaximumHeight(200)
        self.properties_text.setReadOnly(True)
        properties_layout.addWidget(self.properties_text)
        
        layout.addWidget(properties_group)
        
        layout.addStretch()
        
        return panel
    
    def create_toolbar(self):
        """Create the main toolbar."""
        toolbar = self.addToolBar("Main")
        
        # File operations
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_graph)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_graph)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_graph)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Export operations
        export_egi_action = QAction("Export EGI", self)
        export_egi_action.triggered.connect(self.export_egi)
        toolbar.addAction(export_egi_action)
        
        export_egif_action = QAction("Export EGIF", self)
        export_egif_action.triggered.connect(self.export_egif)
        toolbar.addAction(export_egif_action)
    
    def setup_connections(self):
        """Set up signal connections."""
        self.scene.selectionChanged.connect(self.on_selection_changed)
    
    def update_ui_for_mode(self):
        """Update UI elements based on current workshop mode."""
        is_practice = self.workshop_mode == WorkshopMode.PRACTICE
        
        # Show/hide transformation palette
        self.transformation_palette.setVisible(is_practice)
        
        # Update status widget
        self.status_widget.update_mode(self.workshop_mode)
        
        # Update mode checkboxes
        self.composition_radio.setChecked(self.workshop_mode == WorkshopMode.COMPOSITION)
        self.practice_radio.setChecked(self.workshop_mode == WorkshopMode.PRACTICE)
    
    def set_interaction_mode(self, mode: InteractionMode):
        """Set the current interaction mode."""
        self.interaction_mode = mode
        
        # Update button states
        buttons = [self.select_btn, self.add_cut_btn, self.add_vertex_btn, 
                  self.add_pred_btn, self.ligature_btn]
        for btn in buttons:
            btn.setChecked(False)
        
        if mode == InteractionMode.SELECT:
            self.select_btn.setChecked(True)
        elif mode == InteractionMode.ADD_CUT:
            self.add_cut_btn.setChecked(True)
        elif mode == InteractionMode.ADD_VERTEX:
            self.add_vertex_btn.setChecked(True)
        elif mode == InteractionMode.ADD_PREDICATE:
            self.add_pred_btn.setChecked(True)
        elif mode == InteractionMode.LIGATURE:
            self.ligature_btn.setChecked(True)
    
    def on_mode_changed(self):
        """Handle workshop mode change."""
        if self.composition_radio.isChecked() and not self.practice_radio.isChecked():
            self.workshop_mode = WorkshopMode.COMPOSITION
        elif self.practice_radio.isChecked() and not self.composition_radio.isChecked():
            self.workshop_mode = WorkshopMode.PRACTICE
        else:
            # Ensure exactly one is checked
            if self.sender() == self.composition_radio:
                self.practice_radio.setChecked(False)
                self.workshop_mode = WorkshopMode.COMPOSITION
            else:
                self.composition_radio.setChecked(False)
                self.workshop_mode = WorkshopMode.PRACTICE
        
        self.model.workshop_mode = self.workshop_mode
        self.update_ui_for_mode()
    
    def load_corpus_item(self, corpus_id: str, metadata: dict):
        """Load a corpus item into the editor."""
        try:
            # Clear current graph
            self.new_graph()
            
            # Set source reference
            self.model.source_corpus_id = corpus_id
            
            # Parse EGIF and create drawing elements
            egif = metadata.get("egif", "")
            if egif:
                self.import_egif_to_scene(egif)
            
            # Update status
            self.statusBar().showMessage(f"Loaded: {metadata.get('title', corpus_id)}")
            self.update_status_counts()
            
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load corpus item: {str(e)}")
    
    def import_egif_to_scene(self, egif_text: str):
        """Import EGIF text and create visual elements."""
        # This would integrate with the EGIF parser
        # For now, create a simple example based on the text
        if "Human" in egif_text and "Socrates" in egif_text:
            # Create a simple Human-Socrates example
            self.add_vertex_at(QPointF(200, 200), label="Socrates", label_kind="constant")
            self.add_predicate_at(QPointF(300, 200), "Human")
    
    def validate_graph(self):
        """Validate the current graph and show results."""
        errors = self.model.validate_constraints()
        
        if not errors:
            self.validation_text.setText("✓ Graph is valid according to EG constraints.")
            self.status_widget.update_validation(True)
        else:
            error_text = "Validation Errors:\n\n" + "\n".join(f"• {error}" for error in errors)
            self.validation_text.setText(error_text)
            self.status_widget.update_validation(False, len(errors))
    
    def apply_transformation(self, rule_name: str, description: str):
        """Apply a transformation rule."""
        if self.workshop_mode != WorkshopMode.PRACTICE:
            QMessageBox.information(self, "Mode Error", 
                                  "Transformations are only available in Practice mode.")
            return
        
        # Record current state
        before_state = self.model.to_schema()
        
        # Apply transformation (placeholder implementation)
        success = self.apply_transformation_rule(rule_name)
        
        if success:
            after_state = self.model.to_schema()
            step_id = self.model.add_transformation_step(rule_name, description, 
                                                       before_state, after_state)
            self.statusBar().showMessage(f"Applied transformation: {description}")
        else:
            QMessageBox.warning(self, "Transformation Error", 
                              f"Could not apply transformation: {description}")
    
    def apply_transformation_rule(self, rule_name: str) -> bool:
        """Apply a specific transformation rule (placeholder)."""
        # This would implement the actual transformation logic
        # For now, just return success for demonstration
        return True
    
    def add_vertex_at(self, pos: QPointF, label: str = None, label_kind: str = None) -> str:
        """Add a vertex at the specified position."""
        vid = f"v_{uuid.uuid4().hex[:6]}"
        area_id = self.get_area_at_position(pos)
        
        # Create graphics item
        gfx = QGraphicsEllipseItem(-4, -4, 8, 8)
        gfx.setBrush(QBrush(QColor(0, 0, 0)))
        gfx.setPen(QPen(QColor(0, 0, 0), 2))
        gfx.setPos(pos)
        gfx.setFlag(QGraphicsItem.ItemIsMovable, True)
        gfx.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.scene.addItem(gfx)
        
        # Create vertex item
        vertex = VertexItem(id=vid, pos=pos, area_id=area_id, gfx=gfx, 
                           label=label, label_kind=label_kind)
        
        # Add label if provided
        if label:
            txt = QGraphicsTextItem(label)
            txt.setDefaultTextColor(QColor(20, 20, 20))
            txt.setPos(QPointF(6, -8))
            txt.setParentItem(gfx)
            vertex.gfx_label = txt
        
        self.model.vertices[vid] = vertex
        return vid
    
    def add_predicate_at(self, pos: QPointF, name: str) -> str:
        """Add a predicate at the specified position."""
        pid = f"p_{uuid.uuid4().hex[:6]}"
        area_id = self.get_area_at_position(pos)
        
        # Create graphics items
        text = QGraphicsTextItem(name)
        rect = text.boundingRect().adjusted(-4, -2, 4, 2)
        rect_item = QGraphicsRectItem(rect)
        rect_item.setBrush(QBrush(QColor(255, 255, 255)))
        rect_item.setPen(QPen(QColor(0, 0, 0, 60), 1))
        
        rect_item.setPos(pos)
        text.setParentItem(rect_item)
        text.setPos(4, 2)
        
        rect_item.setFlag(QGraphicsItem.ItemIsMovable, True)
        rect_item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        self.scene.addItem(rect_item)
        
        # Create predicate item
        predicate = PredicateItem(id=pid, name=name, pos=pos, area_id=area_id,
                                 gfx_text=text, gfx_rect=rect_item)
        self.model.predicates[pid] = predicate
        return pid
    
    def get_area_at_position(self, pos: QPointF) -> str:
        """Get the area ID at the specified position."""
        # Check if position is inside any cut
        for cut_id, cut in self.model.cuts.items():
            if cut.rect.contains(pos):
                return cut_id
        return self.model.sheet_id
    
    def update_status_counts(self):
        """Update the status widget with current element counts."""
        cuts = len(self.model.cuts)
        vertices = len(self.model.vertices)
        predicates = len(self.model.predicates)
        self.status_widget.update_counts(cuts, vertices, predicates)
    
    def on_selection_changed(self):
        """Handle selection changes."""
        selected_items = self.scene.selectedItems()
        if selected_items:
            # Show properties of selected item
            item = selected_items[0]
            self.show_item_properties(item)
        else:
            self.properties_text.clear()
    
    def show_item_properties(self, item: QGraphicsItem):
        """Show properties of the selected item."""
        properties = []
        
        # Find the corresponding model item
        for vid, vertex in self.model.vertices.items():
            if vertex.gfx == item:
                properties.append(f"Type: Vertex")
                properties.append(f"ID: {vid}")
                properties.append(f"Area: {vertex.area_id}")
                if vertex.label:
                    properties.append(f"Label: {vertex.label}")
                    properties.append(f"Kind: {vertex.label_kind}")
                break
        
        for pid, predicate in self.model.predicates.items():
            if predicate.gfx_rect == item:
                properties.append(f"Type: Predicate")
                properties.append(f"ID: {pid}")
                properties.append(f"Name: {predicate.name}")
                properties.append(f"Area: {predicate.area_id}")
                if predicate.arity:
                    properties.append(f"Arity: {predicate.arity}")
                break
        
        for cid, cut in self.model.cuts.items():
            if cut.gfx == item:
                properties.append(f"Type: Cut")
                properties.append(f"ID: {cid}")
                properties.append(f"Parent: {cut.parent_id or 'Sheet'}")
                if cut.label:
                    properties.append(f"Label: {cut.label}")
                break
        
        self.properties_text.setText("\n".join(properties))
    
    # File operations
    def new_graph(self):
        """Create a new empty graph."""
        self.scene.clear()
        self.model = ErgasterionModel()
        self.model.workshop_mode = self.workshop_mode
        self.update_status_counts()
        self.validation_text.clear()
        self.properties_text.clear()
        self.statusBar().showMessage("New graph created")
    
    def open_graph(self):
        """Open a graph from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Graph", "", "JSON Files (*.json);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.load_from_schema(data)
                self.statusBar().showMessage(f"Opened: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Open Error", f"Failed to open file: {str(e)}")
    
    def save_graph(self):
        """Save the current graph to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Graph", "", "JSON Files (*.json);;All Files (*)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.model.to_schema(), f, indent=2)
                self.statusBar().showMessage(f"Saved: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file: {str(e)}")
    
    def export_egi(self):
        """Export to EGI format."""
        # This would integrate with the EGI export system
        QMessageBox.information(self, "Export", "EGI export functionality will be implemented.")
    
    def export_egif(self):
        """Export to EGIF format."""
        # This would integrate with the EGIF generator
        QMessageBox.information(self, "Export", "EGIF export functionality will be implemented.")
    
    def load_from_schema(self, schema: dict):
        """Load graph from schema data."""
        # This would implement the full loading logic
        self.new_graph()
        # Implementation would go here
    
    def eventFilter(self, obj, event):
        """Handle mouse events for drawing interactions."""
        # This would implement the mouse interaction logic
        # Similar to the original drawing_editor.py but enhanced
        return super().eventFilter(obj, event)


def main():
    """Main entry point for Ergasterion Composer/Editor."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Ergasterion")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Arisbe Project")
    
    # Create and show main window
    window = ErgasterionComposerEditor()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

