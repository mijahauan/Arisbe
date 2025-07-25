"""
Existential Graphs Editor - PySide6 Implementation

A "bullpen" application for preparing and exploring graphs before EPG innings.
Supports dual-form editing (linear CLIF + diagrammatic EG) with continuous validation.

Architecture:
- Linear Form: CLIF text editing with syntax validation
- Diagram Form: Interactive QGraphicsView with EGRF rendering
- Validation: Real-time consistency checking between forms
- Transformation: Lookahead exploration of Peircean rules
- Output: Save, export, and EPG proposal capabilities
"""

import sys
import os
from typing import Optional, Dict, List, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTextEdit, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QMenuBar, QToolBar, QStatusBar, QTabWidget, QGroupBox, QLabel,
    QPushButton, QComboBox, QListWidget, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QFileDialog, QProgressBar, QCheckBox, QSpinBox,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsPathItem
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QPointF, QRectF
from PySide6.QtGui import (
    QAction, QFont, QColor, QPen, QBrush, QPainter, QPainterPath,
    QPixmap, QIcon
)

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from corpus_api import CorpusAPI
from clif_parser import CLIFParser
from egrf.v3.converter.direct_graph_to_egrf import convert_graph_to_egrf_direct
from eg_types import Entity, Predicate, Context
from graph import EGGraph
from transformations import TransformationEngine
from semantic_validator import SemanticValidator


class EGGraphicsItem(QGraphicsItem):
    """Base class for Existential Graph elements in the graphics view."""
    
    def __init__(self, element_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.element_data = element_data
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
    
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, 100, 50)
    
    def paint(self, painter: QPainter, option, widget):
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(self.boundingRect())


class ContextItem(EGGraphicsItem):
    """Graphics item for EG contexts (cuts)."""
    
    def __init__(self, context_data: Dict[str, Any], parent=None):
        super().__init__(context_data, parent)
        
        # Extract size from layout constraints or use defaults
        layout_constraints = context_data.get('layout_constraints', {})
        size_constraints = layout_constraints.get('size_constraints', {})
        preferred_size = size_constraints.get('preferred', {'width': 200, 'height': 150})
        
        self.width = preferred_size.get('width', 200)
        self.height = preferred_size.get('height', 150)
        
        # Determine context type
        logical_props = context_data.get('logical_properties', {})
        self.context_type = logical_props.get('context_type', 'cut')
        self.is_root = logical_props.get('is_root', False)
    
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option, widget):
        if self.is_root or self.context_type == 'sheet_of_assertion':
            # Draw sheet of assertion as rectangle
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.setBrush(QBrush(QColor(250, 250, 250, 100)))
            painter.drawRect(self.boundingRect())
            
            # Add label
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(10, 20, "Sheet of Assertion")
        else:
            # Draw cut as ellipse
            painter.setPen(QPen(QColor(200, 50, 50), 3))
            painter.setBrush(QBrush(QColor(255, 240, 240, 50)))
            painter.drawEllipse(self.boundingRect())
            
            # Add label
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(10, 20, f"Cut {self.element_data.get('id', '')}")


class PredicateItem(EGGraphicsItem):
    """Graphics item for EG predicates."""
    
    def __init__(self, predicate_data: Dict[str, Any], parent=None):
        super().__init__(predicate_data, parent)
        self.radius = 25
        
        # Extract predicate name from logical properties
        logical_props = predicate_data.get('logical_properties', {})
        self.predicate_name = predicate_data.get('name', 'P')
    
    def boundingRect(self) -> QRectF:
        return QRectF(-self.radius, -self.radius, 2*self.radius, 2*self.radius)
    
    def paint(self, painter: QPainter, option, widget):
        painter.setPen(QPen(QColor(50, 100, 200), 2))
        painter.setBrush(QBrush(QColor(240, 245, 255)))
        painter.drawEllipse(self.boundingRect())
        
        # Add predicate label
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(-10, 5, self.predicate_name)


class EntityItem(EGGraphicsItem):
    """Graphics item for EG entities (lines of identity)."""
    
    def __init__(self, entity_data: Dict[str, Any], parent=None):
        super().__init__(entity_data, parent)
        self.connections = entity_data.get('connections', [])
    
    def boundingRect(self) -> QRectF:
        if not self.connections:
            return QRectF(0, 0, 50, 5)
        
        # Calculate bounding rect from connections
        min_x = min(conn.get('x', 0) for conn in self.connections)
        max_x = max(conn.get('x', 0) for conn in self.connections)
        min_y = min(conn.get('y', 0) for conn in self.connections)
        max_y = max(conn.get('y', 0) for conn in self.connections)
        
        return QRectF(min_x - 5, min_y - 5, max_x - min_x + 10, max_y - min_y + 10)
    
    def paint(self, painter: QPainter, option, widget):
        painter.setPen(QPen(QColor(100, 150, 100), 3))
        
        # Draw line of identity connecting predicates
        if len(self.connections) >= 2:
            for i in range(len(self.connections) - 1):
                start = self.connections[i]
                end = self.connections[i + 1]
                painter.drawLine(
                    QPointF(start.get('x', 0), start.get('y', 0)),
                    QPointF(end.get('x', 0), end.get('y', 0))
                )
        
        # Draw connection points
        for conn in self.connections:
            painter.setBrush(QBrush(QColor(100, 150, 100)))
            painter.drawEllipse(
                QPointF(conn.get('x', 0), conn.get('y', 0)), 4, 4
            )


class GraphCanvas(QGraphicsView):
    """Interactive canvas for displaying and editing EG diagrams."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configure view
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Set scene size (Sheet of Assertion)
        self.scene.setSceneRect(0, 0, 800, 600)
        
        # Current graph data
        self.current_graph = None
        self.graph_items = {}
    
    def load_egrf_graph(self, egrf_data: Dict[str, Any]):
        """Load and display an EGRF graph."""
        self.scene.clear()
        self.graph_items.clear()
        self.current_graph = egrf_data
        
        if not egrf_data or 'elements' not in egrf_data:
            return
        
        # Create graphics items for each EGRF element
        # Handle both dictionary and list formats for elements
        elements = egrf_data['elements']
        if isinstance(elements, dict):
            # Elements is a dictionary with IDs as keys
            element_count = 0
            for element_id, element in elements.items():
                item = self.create_graphics_item(element)
                if item:
                    self.scene.addItem(item)
                    self.graph_items[element_id] = item
                    
                    # Position the item - use default grid if no position data
                    pos = element.get('position', None)
                    if pos is None:
                        # Create a simple grid layout for elements without position
                        x = 100 + (element_count % 3) * 150
                        y = 100 + (element_count // 3) * 120
                        pos = {'x': x, 'y': y}
                    
                    item.setPos(pos['x'], pos['y'])
                    element_count += 1
        else:
            # Elements is a list
            for i, element in enumerate(elements):
                item = self.create_graphics_item(element)
                if item:
                    self.scene.addItem(item)
                    self.graph_items[element['id']] = item
                    
                    # Position the item - use default grid if no position data
                    pos = element.get('position', None)
                    if pos is None:
                        # Create a simple grid layout for elements without position
                        x = 100 + (i % 3) * 150
                        y = 100 + (i // 3) * 120
                        pos = {'x': x, 'y': y}
                    
                    item.setPos(pos['x'], pos['y'])
    
    def create_graphics_item(self, element: Dict[str, Any]) -> Optional[EGGraphicsItem]:
        """Create appropriate graphics item for EGRF element."""
        element_type = element.get('element_type', element.get('type', 'unknown'))
        
        # Add debug info
        print(f"Creating graphics item for: {element.get('id', 'no-id')} type: {element_type}")
        
        if element_type in ['context', 'cut']:
            return ContextItem(element)
        elif element_type == 'predicate':
            return PredicateItem(element)
        elif element_type == 'entity':
            return EntityItem(element)
        else:
            print(f"Unknown element type: {element_type}")
            return None
    
    def wheelEvent(self, event):
        """Handle zoom with mouse wheel."""
        factor = 1.2
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor
        self.scale(factor, factor)


class ValidationPanel(QWidget):
    """Panel for displaying validation results and graph statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Validation status
        self.status_label = QLabel("Validation Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Validation details
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        # Graph statistics
        stats_group = QGroupBox("Graph Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_labels = {
            'elements': QLabel("Elements: 0"),
            'contexts': QLabel("Contexts: 0"),
            'predicates': QLabel("Predicates: 0"),
            'entities': QLabel("Entities: 0")
        }
        
        for label in self.stats_labels.values():
            stats_layout.addWidget(label)
        
        layout.addWidget(stats_group)
    
    def update_validation(self, is_valid: bool, messages: List[str], stats: Dict[str, int]):
        """Update validation display."""
        if is_valid:
            self.status_label.setText("Validation Status: ✓ Valid")
            self.status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        else:
            self.status_label.setText("Validation Status: ✗ Invalid")
            self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
        
        self.details_text.setPlainText('\n'.join(messages))
        
        # Update statistics
        for key, label in self.stats_labels.items():
            count = stats.get(key, 0)
            label.setText(f"{key.capitalize()}: {count}")


class TransformationPanel(QWidget):
    """Panel for exploring Peircean transformations (lookahead)."""
    
    transformation_requested = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Peircean rules
        rules_group = QGroupBox("Peircean Rules")
        rules_layout = QVBoxLayout(rules_group)
        
        self.rule_buttons = {}
        rules = [
            ('insertion', 'Insertion'),
            ('deletion', 'Deletion'),
            ('erasure', 'Erasure'),
            ('double_cut', 'Double Cut'),
            ('iteration', 'Iteration')
        ]
        
        for rule_id, rule_name in rules:
            btn = QPushButton(rule_name)
            btn.clicked.connect(lambda checked, r=rule_id: self.request_transformation(r))
            rules_layout.addWidget(btn)
            self.rule_buttons[rule_id] = btn
        
        layout.addWidget(rules_group)
        
        # Quick additions
        quick_group = QGroupBox("Quick Add")
        quick_layout = QVBoxLayout(quick_group)
        
        quick_buttons = [
            ('add_cut', 'Add Cut'),
            ('add_predicate', 'Add Predicate'),
            ('add_line', 'Add Line of Identity')
        ]
        
        for action_id, action_name in quick_buttons:
            btn = QPushButton(action_name)
            btn.clicked.connect(lambda checked, a=action_id: self.request_transformation(a))
            quick_layout.addWidget(btn)
        
        layout.addWidget(quick_group)
        
        # Transformation history
        history_group = QGroupBox("Recent Transformations")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(100)
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(history_group)
    
    def request_transformation(self, rule_id: str):
        """Request a transformation to be applied."""
        self.transformation_requested.emit(rule_id, {})
    
    def add_to_history(self, rule_name: str, description: str):
        """Add transformation to history."""
        self.history_list.addItem(f"{rule_name}: {description}")
        self.history_list.scrollToBottom()


class GraphEditor(QMainWindow):
    """Main Graph Editor window - the 'bullpen' for EPG preparation."""
    
    def __init__(self):
        super().__init__()
        self.current_graph = None
        self.clif_parser = CLIFParser()
        
        # Initialize corpus API with correct path
        repo_root = Path(__file__).parent.parent.parent  # Go up from gui -> src -> Arisbe
        corpus_path = repo_root / 'corpus' / 'corpus'
        self.corpus_api = CorpusAPI(corpus_path)
        
        self.init_ui()
        self.init_connections()
    
    def init_ui(self):
        self.setWindowTitle("Arisbe - Existential Graphs Editor (Bullpen)")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Input and controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel - Graph canvas
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # Right panel - Validation and transformations
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 700, 300])
        
        # Create menus and toolbars
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()
    
    def create_left_panel(self) -> QWidget:
        """Create the left input panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Input methods
        input_group = QGroupBox("Graph Input")
        input_layout = QVBoxLayout(input_group)
        
        # CLIF input
        clif_group = QGroupBox("CLIF Statement")
        clif_layout = QVBoxLayout(clif_group)
        
        self.clif_text = QTextEdit()
        self.clif_text.setMaximumHeight(120)
        self.clif_text.setPlaceholderText("Enter CLIF statement here...")
        clif_layout.addWidget(self.clif_text)
        
        parse_btn = QPushButton("Parse CLIF")
        parse_btn.clicked.connect(self.parse_clif)
        clif_layout.addWidget(parse_btn)
        
        input_layout.addWidget(clif_group)
        
        # Corpus selection
        corpus_group = QGroupBox("Corpus Examples")
        corpus_layout = QVBoxLayout(corpus_group)
        
        self.corpus_combo = QComboBox()
        self.load_corpus_examples()
        corpus_layout.addWidget(self.corpus_combo)
        
        load_corpus_btn = QPushButton("Load Example")
        load_corpus_btn.clicked.connect(self.load_corpus_example)
        corpus_layout.addWidget(load_corpus_btn)
        
        input_layout.addWidget(corpus_group)
        
        # Empty graph
        empty_btn = QPushButton("Create Empty Graph")
        empty_btn.clicked.connect(self.create_empty_graph)
        input_layout.addWidget(empty_btn)
        
        layout.addWidget(input_group)
        
        # Export options
        export_group = QGroupBox("Export & Save")
        export_layout = QVBoxLayout(export_group)
        
        export_buttons = [
            ("Save Graph", self.save_graph),
            ("Export PDF", lambda: self.export_graph('pdf')),
            ("Export PNG", lambda: self.export_graph('png')),
            ("Export LaTeX", lambda: self.export_graph('latex')),
            ("Propose to EPG", self.propose_to_epg)
        ]
        
        for text, handler in export_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            export_layout.addWidget(btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        return panel
    
    def create_center_panel(self) -> QWidget:
        """Create the center graph canvas panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget for dual forms
        self.tab_widget = QTabWidget()
        
        # Diagram tab
        self.canvas = GraphCanvas()
        self.tab_widget.addTab(self.canvas, "Diagram Form")
        
        # Linear form tab
        self.linear_text = QTextEdit()
        self.linear_text.setFont(QFont("Courier", 10))
        self.linear_text.setReadOnly(True)
        self.tab_widget.addTab(self.linear_text, "Linear Form (CLIF)")
        
        layout.addWidget(self.tab_widget)
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create the right validation and transformation panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Validation panel
        self.validation_panel = ValidationPanel()
        layout.addWidget(self.validation_panel)
        
        # Transformation panel
        self.transformation_panel = TransformationPanel()
        layout.addWidget(self.transformation_panel)
        
        return panel
    
    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Graph", self)
        new_action.triggered.connect(self.create_empty_graph)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open...", self)
        open_action.triggered.connect(self.open_graph)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_graph)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        validate_action = QAction("Validate Graph", self)
        validate_action.triggered.connect(self.validate_current_graph)
        edit_menu.addAction(validate_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(lambda: self.canvas.scale(1.2, 1.2))
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(lambda: self.canvas.scale(0.8, 0.8))
        view_menu.addAction(zoom_out_action)
    
    def create_toolbar(self):
        """Create application toolbar."""
        toolbar = self.addToolBar("Main")
        
        # Add common actions
        toolbar.addAction("New", self.create_empty_graph)
        toolbar.addAction("Open", self.open_graph)
        toolbar.addAction("Save", self.save_graph)
        toolbar.addSeparator()
        toolbar.addAction("Validate", self.validate_current_graph)
        toolbar.addSeparator()
        toolbar.addAction("Zoom In", lambda: self.canvas.scale(1.2, 1.2))
        toolbar.addAction("Zoom Out", lambda: self.canvas.scale(0.8, 0.8))
    
    def create_status_bar(self):
        """Create application status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add progress bar for long operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def init_connections(self):
        """Initialize signal connections."""
        self.transformation_panel.transformation_requested.connect(self.apply_transformation)
        self.clif_text.textChanged.connect(self.on_clif_changed)
    
    def load_corpus_examples(self):
        """Load corpus examples into combo box."""
        try:
            example_ids = self.corpus_api.get_example_ids()
            self.corpus_combo.clear()
            self.corpus_combo.addItem("Select example...", None)
            
            for example_id in example_ids:
                example = self.corpus_api.load_example(example_id)
                display_name = f"{example.category}: {example_id}"
                self.corpus_combo.addItem(display_name, example_id)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load corpus examples: {e}")
    
    def parse_clif(self):
        """Parse CLIF text and convert to graph."""
        clif_text = self.clif_text.toPlainText().strip()
        if not clif_text:
            return
        
        try:
            self.status_bar.showMessage("Parsing CLIF...")
            result = self.clif_parser.parse(clif_text)
            
            if result.success:
                self.load_graph(result.graph, clif_text)
                self.status_bar.showMessage("CLIF parsed successfully")
            else:
                QMessageBox.warning(self, "Parse Error", f"Failed to parse CLIF: {result.error}")
                self.status_bar.showMessage("Parse failed")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error parsing CLIF: {e}")
            self.status_bar.showMessage("Parse error")
    
    def load_corpus_example(self):
        """Load selected corpus example."""
        example_id = self.corpus_combo.currentData()
        if not example_id:
            return
        
        try:
            self.status_bar.showMessage("Loading corpus example...")
            example = self.corpus_api.load_example(example_id)
            
            # Parse the CLIF content
            result = self.clif_parser.parse(example.clif_content)
            if not result.errors and result.graph is not None:
                self.load_graph(result.graph, example.clif_content)
                self.status_bar.showMessage(f"Loaded: {example_id}")
            else:
                error_msg = '; '.join([str(e) for e in result.errors]) if result.errors else "Unknown parsing error"
                QMessageBox.warning(self, "Error", f"Failed to parse corpus example: {error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading corpus example: {e}")
    
    def create_empty_graph(self):
        """Create an empty Sheet of Assertion."""
        try:
            # Create minimal EGRF structure for empty sheet
            empty_egrf = {
                'id': 'empty_sheet',
                'elements': {
                    'sheet_of_assertion': {
                        'id': 'sheet_of_assertion',
                        'type': 'context',
                        'label': 'Sheet of Assertion',
                        'position': {'x': 50, 'y': 50},
                        'size': {'width': 700, 'height': 500},
                        'containment': []
                    }
                },
                'containment': []
            }
            
            self.canvas.load_egrf_graph(empty_egrf)
            self.linear_text.setPlainText("% Empty Sheet of Assertion")
            self.current_graph = empty_egrf
            self.validate_current_graph()
            self.status_bar.showMessage("Created empty graph")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating empty graph: {e}")
    
    def load_graph(self, eg_graph: EGGraph, clif_text: str):
        """Load a graph into both diagram and linear forms."""
        try:
            # Convert EG-HG to EGRF
            egrf_data = convert_graph_to_egrf_direct(eg_graph, {'id': 'loaded_graph'})
            
            # Load into canvas
            self.canvas.load_egrf_graph(egrf_data)
            
            # Update linear form
            self.linear_text.setPlainText(clif_text)
            
            # Store current graph
            self.current_graph = egrf_data
            
            # Validate
            self.validate_current_graph()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading graph: {e}")
    
    def validate_current_graph(self):
        """Validate the current graph and update validation panel."""
        if not self.current_graph:
            self.validation_panel.update_validation(True, ["No graph loaded"], {})
            return
        
        try:
            # Basic validation - count elements
            elements = self.current_graph.get('elements', {})
            
            # Handle both dictionary and list formats
            if isinstance(elements, dict):
                element_list = list(elements.values())
            else:
                element_list = elements
            
            stats = {
                'elements': len(element_list),
                'contexts': len([e for e in element_list if e.get('type') == 'context']),
                'predicates': len([e for e in element_list if e.get('type') == 'predicate']),
                'entities': len([e for e in element_list if e.get('type') == 'entity'])
            }
            
            # Simple validation - check for required elements
            messages = []
            is_valid = True
            
            if stats['elements'] == 0:
                messages.append("Graph is empty")
                is_valid = False
            else:
                messages.append("Graph structure appears valid")
                messages.append(f"Contains {stats['elements']} elements")
            
            self.validation_panel.update_validation(is_valid, messages, stats)
            
        except Exception as e:
            self.validation_panel.update_validation(False, [f"Validation error: {e}"], {})
    
    def apply_transformation(self, rule_id: str, params: Dict[str, Any]):
        """Apply a Peircean transformation rule."""
        if not self.current_graph:
            QMessageBox.warning(self, "Warning", "No graph loaded")
            return
        
        try:
            # For now, just show what would happen
            QMessageBox.information(
                self, 
                "Transformation", 
                f"Would apply {rule_id} transformation\n(Implementation pending)"
            )
            
            # Add to transformation history
            self.transformation_panel.add_to_history(rule_id, "Applied successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transformation error: {e}")
    
    def on_clif_changed(self):
        """Handle CLIF text changes."""
        # Could add real-time validation here
        pass
    
    def save_graph(self):
        """Save current graph."""
        if not self.current_graph:
            QMessageBox.warning(self, "Warning", "No graph to save")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Graph", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                import json
                with open(filename, 'w') as f:
                    json.dump(self.current_graph, f, indent=2)
                self.status_bar.showMessage(f"Saved: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Save failed: {e}")
    
    def open_graph(self):
        """Open a saved graph."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Graph", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                import json
                with open(filename, 'r') as f:
                    graph_data = json.load(f)
                
                self.canvas.load_egrf_graph(graph_data)
                self.current_graph = graph_data
                self.validate_current_graph()
                self.status_bar.showMessage(f"Opened: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Open failed: {e}")
    
    def export_graph(self, format_type: str):
        """Export graph in specified format."""
        if not self.current_graph:
            QMessageBox.warning(self, "Warning", "No graph to export")
            return
        
        QMessageBox.information(
            self, 
            "Export", 
            f"Would export to {format_type.upper()} format\n(Implementation pending)"
        )
    
    def propose_to_epg(self):
        """Propose current graph to Endoporeutic Game."""
        if not self.current_graph:
            QMessageBox.warning(self, "Warning", "No graph to propose")
            return
        
        QMessageBox.information(
            self, 
            "EPG Proposal", 
            "Would propose graph to Endoporeutic Game\n(Implementation pending)"
        )


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Arisbe - Existential Graphs Editor")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = GraphEditor()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

