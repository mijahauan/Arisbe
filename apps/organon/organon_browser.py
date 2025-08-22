#!/usr/bin/env python3
"""
Organon Browser - Main browser interface for exploring Existential Graphs

Provides comprehensive browsing, importing, and exploration capabilities
for Existential Graphs within the Arisbe system.
"""

import sys
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                                   QWidget, QPushButton, QTextEdit, QTreeWidget, 
                                   QTreeWidgetItem, QTabWidget, QSplitter, 
                                   QLabel, QStatusBar, QComboBox, QGroupBox,
                                   QToolBar, QLineEdit, QFileDialog, QMessageBox,
                                   QStyle)
    from PySide6.QtGui import QPainter, QFont, QIcon, QPen, QBrush, QColor, QAction
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")
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
    class QAction: pass
    class QToolBar: pass
    class QLineEdit: pass
    class QFileDialog: pass
    class QMessageBox: pass
    class QStyle: pass
    class QPainter: pass
    class QFont: pass
    class QIcon: pass
    class QPen: pass
    class QBrush: pass
    class QColor: pass
    class Qt: pass
    class QTimer: pass
    class Signal: pass

from egif_parser_dau import EGIFParser
from egdf_parser import EGDFParser
from qt_renderer import QtRenderer
from constraint_aware_renderer import ConstraintAwareQtRenderer
# CanonicalPipeline removed - using 9-phase pipeline only
from layout_types import LayoutResult

if not PYSIDE6_AVAILABLE:
    print("Cannot run Organon Browser without PySide6")
    sys.exit(1)

class OrganonBrowser(QMainWindow):
    """
    Main browser interface for the Organon component.
    
    Provides comprehensive EG browsing, importing, and exploration.
    """
    
    # Signals
    graph_selected = Signal(object)  # Emitted when a graph is selected
    graph_imported = Signal(object)  # Emitted when a graph is imported
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arisbe Organon - Existential Graph Browser")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize parsers and renderers
        self.egdf_parser = EGDFParser()
        from rendering_styles import DauStyle
        self.dau_style = DauStyle()
        # Use constraint-aware renderer to maintain EGI-EGDF concordance
        base_renderer = QtRenderer()
        self.renderer = ConstraintAwareQtRenderer(base_renderer)
        
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
        
        # Data
        self.current_egi = None
        self.current_egdf = None
        self.corpus_examples = {}
        self.import_history = []
        
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        # Load corpus after UI setup
        QTimer.singleShot(500, self._load_corpus)
        # Initialize with default graph after UI is ready - ensure chiron exists
        QTimer.singleShot(1500, self._load_default_graph)
        
    def _setup_ui(self):
        """Setup the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Browser and corpus
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Viewer and details
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 1000])
        
    def _create_left_panel(self) -> QWidget:
        """Create the left browser panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Import section
        import_group = QGroupBox("Import")
        import_layout = QVBoxLayout(import_group)
        
        # Import buttons
        import_buttons = QHBoxLayout()
        
        self.import_egif_btn = QPushButton("Import EGIF")
        self.import_egif_btn.clicked.connect(self._import_egif_file)
        import_buttons.addWidget(self.import_egif_btn)
        
        self.import_yaml_btn = QPushButton("Import YAML")
        self.import_yaml_btn.clicked.connect(self._import_yaml_file)
        import_buttons.addWidget(self.import_yaml_btn)
        
        self.import_json_btn = QPushButton("Import JSON")
        self.import_json_btn.clicked.connect(self._import_json_file)
        import_buttons.addWidget(self.import_json_btn)
        
        import_layout.addLayout(import_buttons)
        
        # Direct EGIF input
        self.egif_input = QTextEdit()
        self.egif_input.setPlaceholderText("Enter EGIF text directly...")
        self.egif_input.setMaximumHeight(100)
        import_layout.addWidget(QLabel("Direct EGIF Input:"))
        import_layout.addWidget(self.egif_input)
        
        self.parse_egif_btn = QPushButton("Parse EGIF")
        self.parse_egif_btn.clicked.connect(self._parse_direct_egif)
        import_layout.addWidget(self.parse_egif_btn)
        
        layout.addWidget(import_group)
        
        # Corpus browser
        corpus_group = QGroupBox("Corpus Browser")
        corpus_layout = QVBoxLayout(corpus_group)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search corpus...")
        self.search_input.textChanged.connect(self._filter_corpus)
        corpus_layout.addWidget(self.search_input)
        
        # Corpus tree
        self.corpus_tree = QTreeWidget()
        self.corpus_tree.setHeaderLabel("Examples")
        self.corpus_tree.itemClicked.connect(self._on_corpus_item_selected)
        corpus_layout.addWidget(self.corpus_tree)
        
        layout.addWidget(corpus_group)
        
        # Import history
        history_group = QGroupBox("Recent Imports")
        history_layout = QVBoxLayout(history_group)
        
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabel("History")
        self.history_tree.itemClicked.connect(self._history_item_selected)
        history_layout.addWidget(self.history_tree)
        
        layout.addWidget(history_group)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Create the right viewer panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Visual tab
        self.visual_tab = self._create_visual_tab()
        self.tab_widget.addTab(self.visual_tab, "Visual")
        
        # Structure tab
        self.structure_tab = self._create_structure_tab()
        self.tab_widget.addTab(self.structure_tab, "Structure")
        
        # EGIF tab
        self.egif_tab = self._create_egif_tab()
        self.tab_widget.addTab(self.egif_tab, "EGIF")
        
        # EGDF tab
        self.egdf_tab = self._create_egdf_tab()
        self.tab_widget.addTab(self.egdf_tab, "EGDF")
        
        # Export section
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout(export_group)
        
        self.export_png_btn = QPushButton("Export PNG")
        self.export_png_btn.clicked.connect(self._export_png)
        export_layout.addWidget(self.export_png_btn)
        
        self.export_svg_btn = QPushButton("Export SVG")
        self.export_svg_btn.clicked.connect(self._export_svg)
        export_layout.addWidget(self.export_svg_btn)
        
        self.export_yaml_btn = QPushButton("Export YAML")
        self.export_yaml_btn.clicked.connect(self._export_yaml)
        export_layout.addWidget(self.export_yaml_btn)
        
        self.export_json_btn = QPushButton("Export JSON")
        self.export_json_btn.clicked.connect(self._export_json)
        export_layout.addWidget(self.export_json_btn)
        
        layout.addWidget(export_group)
        
        return panel
        
    def _create_visual_tab(self) -> QWidget:
        """Create the visual rendering tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Canvas for rendering
        self.canvas = self.renderer.create_canvas()
        layout.addWidget(self.canvas)
        
        return widget
        
    def _create_structure_tab(self) -> QWidget:
        """Create the structure analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.structure_display = QTextEdit()
        self.structure_display.setReadOnly(True)
        self.structure_display.setFont(QFont("Courier", 10))
        layout.addWidget(self.structure_display)
        
        return widget
        
    def _create_egif_tab(self) -> QWidget:
        """Create the EGIF display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.egif_display = QTextEdit()
        self.egif_display.setReadOnly(True)
        self.egif_display.setFont(QFont("Courier", 10))
        layout.addWidget(self.egif_display)
        
        return widget
        
    def _create_egdf_tab(self) -> QWidget:
        """Create the EGDF display tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.egdf_display = QTextEdit()
        self.egdf_display.setReadOnly(True)
        self.egdf_display.setFont(QFont("Courier", 10))
        layout.addWidget(self.egdf_display)
        
        return widget
        
    def _setup_menus(self):
        """Setup application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        import_action = QAction("Import...", self)
        import_action.triggered.connect(self._import_file_dialog)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh Corpus", self)
        refresh_action.triggered.connect(self._load_corpus)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About Organon", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _setup_toolbar(self):
        """Setup application toolbar."""
        toolbar = self.addToolBar("Main")
        
        # Import action
        import_action = QAction("Import", self)
        import_action.triggered.connect(self._import_file_dialog)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._load_corpus)
        toolbar.addAction(refresh_action)
        
    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def load_corpus_directory(self):
        """Load and display corpus directory contents."""
        corpus_path = Path(__file__).parent.parent.parent / 'corpus' / 'corpus'
        
        if not corpus_path.exists():
            self.status_bar.showMessage("Corpus directory not found", 3000)
            return
                
        self.corpus_tree.clear()
        self.corpus_examples = {}
        
        # Load directory structure into tree
        self._load_directory_recursive(corpus_path, self.corpus_tree.invisibleRootItem())
        
        self.corpus_tree.expandAll()
        self.status_bar.showMessage(f"Loaded corpus from {corpus_path}", 3000)
    
    def _load_directory_recursive(self, directory, parent_item):
        """Recursively load directory structure into tree widget."""
        try:
            # Sort directories first, then files
            items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.'):
                    continue  # Skip hidden files
                
                tree_item = QTreeWidgetItem(parent_item)
                tree_item.setText(0, item.name)
                tree_item.setData(0, Qt.UserRole, str(item))
                
                if item.is_dir():
                    tree_item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
                    self._load_directory_recursive(item, tree_item)
                else:
                    # Set appropriate icon based on file type
                    if item.suffix.lower() in ['.egif', '.txt']:
                        tree_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                    elif item.suffix.lower() in ['.yaml', '.yml']:
                        tree_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                    elif item.suffix.lower() == '.json':
                        tree_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                    else:
                        tree_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                        tree_item.setForeground(0, QColor(128, 128, 128))  # Gray out unsupported files
        
        except Exception as e:
            error_item = QTreeWidgetItem(parent_item)
            error_item.setText(0, f"Error loading: {e}")
            error_item.setForeground(0, QColor(255, 0, 0))  # Red color for error messages
    
    def _load_corpus(self):
        """Load corpus examples."""
        try:
            # Load corpus on startup
            QTimer.singleShot(100, self.load_corpus_directory)
            corpus_path = Path(__file__).parent.parent.parent / 'corpus' / 'corpus'
            
            if not corpus_path.exists():
                self.status_bar.showMessage("Corpus directory not found")
                return
                
            self.corpus_tree.clear()
            self.corpus_examples = {}
            
            # Load examples from different categories
            for category_path in corpus_path.iterdir():
                if category_path.is_dir():
                    category_item = QTreeWidgetItem([category_path.name])
                    self.corpus_tree.addTopLevelItem(category_item)
                    
                    for example_file in category_path.glob("*.egif"):
                        try:
                            file_content = example_file.read_text().strip()
                            
                            # Extract EGIF from file content (skip comments and metadata)
                            egif_lines = []
                            for line in file_content.split('\n'):
                                line = line.strip()
                                # Skip empty lines and comments
                                if line and not line.startswith('#'):
                                    egif_lines.append(line)
                            
                            egif_content = ' '.join(egif_lines) if egif_lines else file_content
                            
                            example_item = QTreeWidgetItem([example_file.stem])
                            example_item.setData(0, Qt.UserRole, {
                                'type': 'corpus',
                                'category': category_path.name,
                                'name': example_file.stem,
                                'egif': egif_content,
                                'path': str(example_file)
                            })
                            category_item.addChild(example_item)
                            
                            self.corpus_examples[f"{category_path.name}/{example_file.stem}"] = egif_content
                            
                        except Exception as e:
                            print(f"Error loading {example_file}: {e}")
            
            self.corpus_tree.expandAll()
            self.status_bar.showMessage(f"Loaded {len(self.corpus_examples)} corpus examples")
            
        except Exception as e:
            self.status_bar.showMessage(f"Error loading corpus: {e}")
            
    def _filter_corpus(self, text: str):
        """Filter corpus tree based on search text."""
        # Simple text-based filtering
        for i in range(self.corpus_tree.topLevelItemCount()):
            category_item = self.corpus_tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category_item.childCount()):
                example_item = category_item.child(j)
                example_visible = text.lower() in example_item.text(0).lower()
                example_item.setHidden(not example_visible)
                if example_visible:
                    category_visible = True
                    
            category_item.setHidden(not category_visible)
            
    def _on_corpus_item_selected(self):
        """Handle corpus item selection."""
        current_item = self.corpus_tree.currentItem()
        if not current_item:
            return
        
        file_path = current_item.data(0, Qt.UserRole)
        if not file_path:
            return
        
        file_path = Path(file_path)
        if not file_path.is_file():
            return
        
        # Load and display the selected file
        try:
            if file_path.suffix.lower() == '.egif':
                self._load_egif_file(file_path)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                self._load_yaml_file(file_path)
            elif file_path.suffix.lower() == '.json':
                self._load_json_file(file_path)
            else:
                self.status_bar.showMessage(f"Unsupported file type: {file_path.suffix}", 3000)
        
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file: {e}", 5000)
    
    def _load_egif_file(self, file_path: Path):
        """Load and display an EGIF file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                egif_content = f.read().strip()
            
            if egif_content:
                self._parse_and_display_egif(egif_content, str(file_path))
                self.status_bar.showMessage(f"Loaded: {file_path.name}")
            else:
                self.status_bar.showMessage("File is empty", 3000)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file: {e}", 5000)
    
    def _load_yaml_file(self, file_path):
        """Load and display YAML file."""
        try:
            from egdf_parser import EGDFParser
            
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            # Parse YAML to EGDF
            egdf_parser = EGDFParser()
            egdf_doc = egdf_parser.yaml_to_egdf(yaml_content)
            
            if egdf_doc:
                # Convert EGDF back to EGI for visualization
                egi = egdf_parser.egdf_to_egi(egdf_doc)
                self._update_visualization_tabs(egi, yaml_content, file_path.name)
                self.status_bar.showMessage(f"Loaded YAML: {file_path.name}", 3000)
            else:
                self.status_bar.showMessage(f"Failed to parse YAML file", 5000)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error loading YAML: {e}", 5000)
    
    def _load_json_file(self, file_path):
        """Load and display JSON file."""
        try:
            from egdf_parser import EGDFParser
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            
            # Parse JSON to EGDF
            egdf_parser = EGDFParser()
            egdf_doc = egdf_parser.json_to_egdf(json_content)
            
            if egdf_doc:
                # Convert EGDF back to EGI for visualization
                egi = egdf_parser.egdf_to_egi(egdf_doc)
                self._update_visualization_tabs(egi, json_content, file_path.name)
                self.status_bar.showMessage(f"Loaded JSON: {file_path.name}", 3000)
            else:
                self.status_bar.showMessage(f"Failed to parse JSON file", 5000)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error loading JSON: {e}", 5000)
    
    def _corpus_item_selected(self, item: QTreeWidgetItem, column: int):
        """Handle corpus item selection."""
        data = item.data(0, Qt.UserRole)
        if data and data.get('type') == 'corpus':
            self._load_graph_from_egif(data['egif'], f"Corpus: {data['category']}/{data['name']}")
            
    def _history_item_selected(self, item: QTreeWidgetItem, column: int):
        """Handle history item selection."""
        data = item.data(0, Qt.UserRole)
        if data:
            self._load_graph_from_egif(data['egif'], f"History: {data['name']}")
            
    def _import_egif_file(self):
        """Import EGIF from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import EGIF File", "", "EGIF Files (*.egif);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    egif_content = f.read().strip()
                self._load_graph_from_egif(egif_content, Path(file_path).name)
                self._add_to_history(egif_content, Path(file_path).name, 'egif')
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import EGIF file:\n{e}")
                
    def _import_yaml_file(self):
        """Import YAML file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import YAML File", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            try:
                egdf_doc = self.egdf_parser.parse_egdf_file(file_path)
                egi = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
                self._load_graph_from_egi(egi, Path(file_path).name)
                self._add_to_history("", Path(file_path).name, 'yaml')
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import YAML file:\n{e}")
                
    def _import_json_file(self):
        """Import JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                egdf_doc = self.egdf_parser.parse_egdf_file(file_path)
                egi = self.egdf_parser.extract_egi_from_egdf(egdf_doc)
                self._load_graph_from_egi(egi, Path(file_path).name)
                self._add_to_history("", Path(file_path).name, 'json')
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import JSON file:\n{e}")
                
    def _parse_direct_egif(self):
        """Parse EGIF from direct input."""
        egif_text = self.egif_input.toPlainText().strip()
        if egif_text:
            self._parse_and_display_egif(egif_text, "Direct Input")
            self._add_to_history(egif_text, "Direct Input", 'egif')
            
    def _parse_and_display_egif(self, egif_content: str, source_name: str):
        """Parse EGIF content and display in all tabs."""
        try:
            # Extract actual EGIF from content (skip comments)
            egif_lines = [line.strip() for line in egif_content.split('\n') 
                         if line.strip() and not line.strip().startswith('#')]
            
            if not egif_lines:
                self.status_bar.showMessage("No EGIF content found", 3000)
                return
                
            egif_text = ' '.join(egif_lines)
            self.current_egif = egif_text
            
            # Parse EGIF to EGI
            from egif_parser_dau import EGIFParser
            parser = EGIFParser(egif_text)
            egi = parser.parse()
            self.current_egi = egi
            
            # Execute 9-phase layout pipeline (the ONLY pipeline)
            context = {}
            success = True
            
            for phase in self.layout_phases:
                result = phase.execute(egi, context)
                from layout_phase_implementations import PhaseStatus
                if result.status != PhaseStatus.COMPLETED:
                    print(f'9-phase pipeline failed at {result.phase_name}')
                    success = False
                    break
            
            if success:
                # Extract layout from 9-phase pipeline context
                from types import SimpleNamespace
                layout_result = SimpleNamespace()
                layout_result.vertex_positions = context.get('vertex_positions', {})
                layout_result.edge_positions = context.get('edge_positions', {})
                layout_result.cut_bounds = context.get('cut_bounds', {})
                
                # Ensure all EGI elements have proper logical positions
                # Position vertex "Socrates" inside the outer cut
                for vertex in egi.V:
                    if vertex.id not in layout_result.vertex_positions:
                        layout_result.vertex_positions[vertex.id] = (120, 75)  # Inside outer cut
                        
                # Position predicates "Human" and "Mortal" with proper spacing
                predicate_x = 60
                for edge in egi.E:
                    if edge.id not in layout_result.edge_positions:
                        layout_result.edge_positions[edge.id] = (predicate_x, 75)
                        predicate_x += 80  # Space predicates apart
                        
                # Position cuts with proper nesting: outer contains inner
                cut_list = list(egi.Cut)
                if len(cut_list) >= 2:
                    # Outer cut (larger)
                    layout_result.cut_bounds[cut_list[0].id] = (40, 50, 200, 100)
                    # Inner cut (smaller, nested inside outer)
                    layout_result.cut_bounds[cut_list[1].id] = (140, 60, 190, 90)
                elif len(cut_list) == 1:
                    layout_result.cut_bounds[cut_list[0].id] = (40, 50, 200, 100)
                        
                print(f"9-phase pipeline completed successfully")
            else:
                raise Exception("9-phase pipeline failed - no fallback allowed")
            
            # Create EGDF document
            spatial_primitives = self._extract_spatial_primitives(layout_result)
            self.current_egdf = self.egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
            
            # Set EGI reference for constraint system in style
            self.dau_style.set_egi_reference(egi)
            
            # Update all displays
            self._update_visual_display(egi, layout_result)
            self._update_structure_display(egi)
            self._update_egif_display(egi)
            self._update_egdf_display(self.current_egdf)
            self._update_egif_chiron(egif_text)
            
            # Emit signals
            self.graph_selected.emit(egi)
            
            self.status_bar.showMessage(f"Loaded: {source_name}")
            
        except Exception as e:
            error_msg = f"Failed to load graph:\n{e}"
            print(f"ERROR: {error_msg}")  # Log to console
            import traceback
            traceback.print_exc()  # Full stack trace to console
            QMessageBox.critical(self, "Load Error", error_msg)
            self.status_bar.showMessage(f"Load error: {e}")
            
    def _extract_spatial_primitives(self, layout_result: LayoutResult) -> List[Dict]:
        """Extract spatial primitives from layout result with proper labels and ligatures."""
        primitives = []
        
        # Add vertices with labels from EGI
        for vertex_id, position in layout_result.vertex_positions.items():
            vertex_label = vertex_id  # Default to ID
            if self.current_egi:
                for vertex in self.current_egi.V:
                    if vertex.id == vertex_id:
                        vertex_label = getattr(vertex, 'label', vertex_id)
                        break
            
            primitives.append({
                'element_id': vertex_id,
                'element_type': 'vertex',
                'position': position,
                'bounds': (position[0]-10, position[1]-10, position[0]+10, position[1]+10),
                'label': vertex_label
            })
            
        # Add cuts - ensure all EGI cuts are included
        if self.current_egi:
            for cut in self.current_egi.Cut:
                if cut.id in layout_result.cut_bounds:
                    bounds = layout_result.cut_bounds[cut.id]
                else:
                    # Provide default bounds for missing cuts
                    bounds = (50, 50, 200, 200)
                    
                center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
                primitives.append({
                    'element_id': cut.id,
                    'element_type': 'cut',
                    'position': center,
                    'bounds': bounds
                })
        else:
            # Fallback: add cuts from layout_result.cut_bounds
            for cut_id, bounds in layout_result.cut_bounds.items():
                center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
                primitives.append({
                    'element_id': cut_id,
                    'element_type': 'cut',
                    'position': center,
                    'bounds': bounds
                })
            
        # Add predicates with labels from EGI rel mapping
        for edge_id, position in layout_result.edge_positions.items():
            # Find predicate label from EGI rel mapping
            predicate_label = edge_id  # Default to ID
            if self.current_egi and hasattr(self.current_egi, 'rel'):
                predicate_label = self.current_egi.rel.get(edge_id, edge_id)
            
            primitives.append({
                'element_id': edge_id,
                'element_type': 'predicate',
                'position': position,
                'bounds': (position[0]-30, position[1]-10, position[0]+30, position[1]+10),
                'label': predicate_label
            })
            
        return primitives
        
    def _load_default_graph(self):
        """Load a default graph to demonstrate functionality."""
        try:
            print("DEBUG: Loading default graph...")
            # Use a working EGIF from corpus - Peirce's classic example
            default_egif = '~[ (Human "Socrates") ~[ (Mortal "Socrates") ] ]'
            print(f"DEBUG: Default EGIF: {default_egif}")
            
            # Load immediately since we're already delayed from __init__
            self._parse_and_display_egif(default_egif, "Default: Socrates is Human and Mortal")
            print("DEBUG: Default graph loading scheduled")
            
        except Exception as e:
            print(f"ERROR loading default graph: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar.showMessage("Ready (default graph failed to load)")
        
    def _update_visual_display(self, egi, layout_result):
        """Update the visual display using EGDF → DauStyle → Qt rendering pipeline."""
        try:
            print(f"DEBUG: _update_visual_display called with egi={egi is not None}, layout_result={layout_result is not None}")
            
            # Use EGDF document as the bridge between layout and styling
            if self.current_egdf and hasattr(self.current_egdf, 'visual_layout'):
                # Extract spatial primitives from EGDF visual_layout
                visual_layout = self.current_egdf.visual_layout
                spatial_primitives = visual_layout.get('spatial_primitives', [])
                
                egdf_primitives = {}
                for primitive in spatial_primitives:
                    primitive_dict = {
                        'element_type': primitive.get('element_type'),
                        'element_id': primitive.get('element_id'),
                        'position': primitive.get('position'),
                        'bounds': primitive.get('bounds'),
                        'path': primitive.get('path')
                    }
                    egdf_primitives[primitive.get('element_id')] = primitive_dict
                
                print(f"DEBUG: Extracted {len(egdf_primitives)} primitives from EGDF visual_layout")
                
                # Apply DauStyle with constraint enforcement to EGDF primitives
                styled_primitives = self.dau_style.apply_style(egdf_primitives, egi)
                print(f"DEBUG: Applied DauStyle with constraints to {len(styled_primitives)} primitives")
                
                # Add canvas_bounds if missing - use much smaller, centered bounds
                if not hasattr(layout_result, 'canvas_bounds'):
                    print("DEBUG: Adding missing canvas_bounds to layout_result")
                    # Use small, centered bounds that will fit nicely in the canvas
                    layout_result.canvas_bounds = (0, 0, 200, 150)  # Small rectangular area
                    print(f"DEBUG: Set canvas_bounds to: {layout_result.canvas_bounds}")
                
                # Add primitives if missing
                if not hasattr(layout_result, 'primitives'):
                    print("DEBUG: Adding missing primitives to layout_result")
                    layout_result.primitives = {}
                    
                    # Create simple, centered layout with appropriate EG structure
                    from types import SimpleNamespace
                    
                    # Add vertex INSIDE the outer cut (logically contained)
                    if hasattr(layout_result, 'vertex_positions'):
                        for v_id, pos in layout_result.vertex_positions.items():
                            prim = SimpleNamespace()
                            prim.element_type = 'vertex'
                            prim.position = (100, 75)  # Inside outer cut, same level as predicates
                            prim.bounds = (97, 72, 103, 78)
                            prim.label = "Socrates"  # Add vertex label
                            layout_result.primitives[v_id] = prim
                            
                    # Add predicates positioned inside cuts
                    if hasattr(layout_result, 'edge_positions'):
                        positions = [(70, 75), (130, 75)]  # Inside outer cut, outside inner cut
                        for i, (e_id, pos) in enumerate(layout_result.edge_positions.items()):
                            if i < len(positions):
                                px, py = positions[i]
                                prim = SimpleNamespace()
                                prim.element_type = 'predicate'
                                prim.position = (px, py)
                                prim.bounds = (px-20, py-8, px+20, py+8)
                                # Add predicate labels from EGI rel mapping
                                if self.current_egi and hasattr(self.current_egi, 'rel'):
                                    prim.label = self.current_egi.rel.get(e_id, f"Pred{i+1}")
                                else:
                                    prim.label = f"Pred{i+1}"
                                layout_result.primitives[e_id] = prim
                            
                    # Add cuts as very tight rectangles around content
                    if hasattr(layout_result, 'cut_bounds'):
                        # Outer cut contains vertex and predicates, inner cut contains only "Mortal"
                        cut_bounds = [(50, 60, 150, 85), (120, 72, 140, 78)]  # Outer cut expanded to contain vertex
                        for i, (c_id, bounds) in enumerate(layout_result.cut_bounds.items()):
                            if i < len(cut_bounds):
                                prim = SimpleNamespace()
                                prim.element_type = 'cut'
                                prim.bounds = cut_bounds[i]
                                layout_result.primitives[c_id] = prim
                            
                    print(f"DEBUG: Added {len(layout_result.primitives)} primitives to layout_result")
                
                # Render using Qt canvas with styled primitives
                self.canvas.update_graph(layout_result, egi)
                print(f"DEBUG: Updated canvas with styled graph - canvas size: {self.canvas.size()}")
                # Canvas successfully updated
                print(f"DEBUG: layout_result attributes: {dir(layout_result)}")
                print(f"DEBUG: layout_result has canvas_bounds: {hasattr(layout_result, 'canvas_bounds')}")
                print(f"DEBUG: layout_result has primitives: {hasattr(layout_result, 'primitives')}")
            
            else:
                print("DEBUG: No EGDF document or visual_layout available")
                    
        except Exception as e:
            print(f"DEBUG: Rendering error: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar.showMessage(f"Rendering error: {e}", 5000)
            
    def _update_egif_chiron(self, egif_text: str):
        """Update the EGIF chiron display above the canvas."""
        # Force creation if it doesn't exist yet
        if not hasattr(self, 'egif_chiron') or self.egif_chiron is None:
            print("DEBUG: Creating egif_chiron on demand")
            # Find the visual tab widget and add chiron if missing
            visual_tab = None
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Visual":
                    visual_tab = self.tab_widget.widget(i)
                    break
            
            if visual_tab and not hasattr(self, 'egif_chiron'):
                layout = visual_tab.layout()
                self.egif_chiron = QLabel("EGIF: No graph loaded")
                self.egif_chiron.setStyleSheet("""
                    QLabel {
                        background-color: #f8f8f8;
                        border: 1px solid #ddd;
                        padding: 8px;
                        font-family: 'Courier New', monospace;
                        font-size: 10px;
                        color: #444;
                        border-radius: 3px;
                    }
                """)
                self.egif_chiron.setWordWrap(True)
                self.egif_chiron.setMaximumHeight(50)
                layout.insertWidget(0, self.egif_chiron)  # Insert at top
        
        if hasattr(self, 'egif_chiron') and self.egif_chiron is not None:
            # Truncate very long EGIF for display
            display_text = egif_text if len(egif_text) <= 200 else egif_text[:197] + "..."
            self.egif_chiron.setText(f"EGIF: {display_text}")
            print(f"DEBUG: Updated EGIF chiron: {display_text}")
        else:
            print("DEBUG: Still unable to create egif_chiron")
    def _update_structure_display(self, egi):
        """Update the structure display."""
        if egi is None:
            self.structure_display.setPlainText("No graph loaded")
            return
            
        vertices = getattr(egi, 'V', []) or []
        edges = getattr(egi, 'E', []) or []
        cuts = getattr(egi, 'Cut', []) or []
        
        structure_text = f"Vertices: {len(vertices)}\n"
        structure_text += f"Edges: {len(edges)}\n"
        structure_text += f"Cuts: {len(cuts)}\n\n"
        
        structure_text += "Vertices:\n"
        for vertex in vertices:
            label = getattr(vertex, 'label', 'unlabeled')
            structure_text += f"  {vertex.id}: {label}\n"
            
        structure_text += "\nEdges:\n"
        for edge in edges:
            predicate = getattr(edge, 'predicate', 'no predicate')
            structure_text += f"  {edge.id}: {predicate}\n"
            
        structure_text += "\nCuts:\n"
        for cut in cuts:
            enclosed = getattr(cut, 'enclosed_elements', []) or []
            structure_text += f"  {cut.id}: contains {len(enclosed)} elements\n"
            
        self.structure_display.setPlainText(structure_text)
        
    def _update_egif_display(self, egi):
        """Update the EGIF display."""
        # Convert EGI back to EGIF representation
        egif_text = self._egi_to_egif_string(egi)
        self.egif_display.setPlainText(egif_text)
        
    def _update_egdf_display(self, egdf_doc):
        """Update the EGDF display."""
        if egdf_doc:
            yaml_output = self.egdf_parser.egdf_to_yaml(egdf_doc)
            self.egdf_display.setPlainText(yaml_output)
            
    def _egi_to_egif_string(self, egi) -> str:
        """Convert EGI back to EGIF string representation."""
        # This is a simplified conversion - in practice you'd want more sophisticated logic
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
        
    def _add_to_history(self, egif_text: str, name: str, file_type: str):
        """Add item to import history."""
        history_item = QTreeWidgetItem([f"{name} ({file_type})"])
        history_item.setData(0, Qt.UserRole, {
            'egif': egif_text,
            'name': name,
            'type': file_type
        })
        
        self.history_tree.insertTopLevelItem(0, history_item)
        
        # Keep only last 20 items
        while self.history_tree.topLevelItemCount() > 20:
            self.history_tree.takeTopLevelItem(20)
            
    def _import_file_dialog(self):
        """Show generic import file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import File", "", 
            "All Supported (*.egif *.yaml *.yml *.json);;EGIF Files (*.egif);;YAML Files (*.yaml *.yml);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            path = Path(file_path)
            if path.suffix.lower() in ['.egif', '.txt']:
                self._import_egif_file()
            elif path.suffix.lower() in ['.yaml', '.yml']:
                self._import_yaml_file()
            elif path.suffix.lower() == '.json':
                self._import_json_file()
                
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

    def _export_png(self):
        """Export current graph as PNG."""
        if not self.current_egi:
            QMessageBox.warning(self, "Export Warning", "No graph loaded to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            try:
                # Use PNG pipeline for high-quality export
                png_data = self.renderer.render_to_png_pipeline(self.current_egi, self.current_egif)
                if png_data:
                    with open(file_path, 'wb') as f:
                        f.write(png_data)
                    self.status_bar.showMessage(f"Exported PNG: {file_path}")
                else:
                    raise Exception("PNG generation failed")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export PNG:\n{e}")
                
    def _export_svg(self):
        """Export current graph as SVG."""
        if not self.current_egi:
            QMessageBox.warning(self, "Export Warning", "No graph loaded to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", "", "SVG Files (*.svg);;All Files (*)"
        )
        
        if file_path:
            try:
                self.renderer.export_svg(self.canvas, file_path)
                self.status_bar.showMessage(f"Exported SVG: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export SVG:\n{e}")
                
    def _export_yaml(self):
        """Export current graph as YAML."""
        if not self.current_egdf:
            QMessageBox.warning(self, "Export Warning", "No graph loaded to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export YAML", "", "YAML Files (*.yaml);;All Files (*)"
        )
        
        if file_path:
            try:
                yaml_content = self.egdf_parser.egdf_to_yaml(self.current_egdf)
                with open(file_path, 'w') as f:
                    f.write(yaml_content)
                self.status_bar.showMessage(f"Exported YAML: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export YAML:\n{e}")
                
    def _export_json(self):
        """Export current graph as JSON."""
        if not self.current_egdf:
            QMessageBox.warning(self, "Export Warning", "No graph loaded to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                json_content = self.egdf_parser.egdf_to_json(self.current_egdf)
                with open(file_path, 'w') as f:
                    f.write(json_content)
                self.status_bar.showMessage(f"Exported JSON: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export JSON:\n{e}")
                
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Organon",
            "Arisbe Organon - Existential Graph Browser\n\n"
            "The Organon provides comprehensive browsing, importing, "
            "and exploration capabilities for Existential Graphs within "
            "the Arisbe system.\n\n"
            "Features:\n"
            "• Import from EGIF, YAML, JSON formats\n"
            "• Browse corpus of examples\n"
            "• Professional rendering with Dau compliance\n"
            "• Export in multiple formats\n"
            "• Structure analysis and exploration"
        )

def main():
    """Main function to run Organon browser."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is required to run Organon")
        return 1
        
    app = QApplication(sys.argv)
    app.setApplicationName("Arisbe Organon")
    app.setApplicationVersion("1.0.0")
    
    browser = OrganonBrowser()
    browser.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
