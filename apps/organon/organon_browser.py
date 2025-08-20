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
    from PySide6.QtWidgets import (
        QMainWindow, QVBoxLayout, QHBoxLayout, 
        QWidget, QPushButton, QTextEdit, QTreeWidget, 
        QTreeWidgetItem, QTabWidget, QSplitter, 
        QLabel, QStatusBar, QFileDialog, QMessageBox,
        QStatusBar, QMenuBar, QMenu, QAction, QToolBar, QLineEdit, QGroupBox
    )
    from PySide6.QtGui import QPainter, QFont, QIcon
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    print("PySide6 not available - install with: pip install PySide6")

from egif_parser_dau import EGIFParser
from egdf_parser import EGDFParser
from canonical_qt_renderer import CanonicalQtRenderer
from canonical import CanonicalPipeline
from layout_types import LayoutResult

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
        
        # Core components
        self.egif_parser = EGIFParser()
        self.egdf_parser = EGDFParser()
        self.pipeline = CanonicalPipeline()
        self.renderer = CanonicalQtRenderer()
        
        # Data
        self.current_egi = None
        self.current_egdf = None
        self.corpus_examples = {}
        self.import_history = []
        
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._load_corpus()
        
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
        self.corpus_tree.itemClicked.connect(self._corpus_item_selected)
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
        
        # Clear existing items
        self.corpus_tree.clear()
        
        # Load corpus structure
        self._load_directory_recursive(corpus_path, self.corpus_tree.invisibleRootItem())
        
        # Expand first level
        for i in range(self.corpus_tree.topLevelItemCount()):
            self.corpus_tree.topLevelItem(i).setExpanded(True)
        
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
                    # Set file icon based on extension
                    if item.suffix.lower() in ['.egif', '.yaml', '.yml', '.json']:
                        tree_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                        # Make supported files selectable
                        tree_item.setFlags(tree_item.flags() | Qt.ItemIsSelectable)
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
            # Load corpus examples from the corpus directory
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
                            with open(example_file, 'r') as f:
                                egif_content = f.read().strip()
                            
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
    
    def _load_egif_file(self, file_path):
        """Load and display EGIF file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                egif_content = f.read().strip()
            
            # Parse EGIF
            from egif_parser_dau import EGIFParser
            parser = EGIFParser(egif_content)
            egi = parser.parse()
            
            # Update visualization tabs
            self._update_visualization_tabs(egi, egif_content, file_path.name)
            
            self.status_bar.showMessage(f"Loaded EGIF: {file_path.name}", 3000)
            
        except Exception as e:
            self.status_bar.showMessage(f"Error parsing EGIF: {e}", 5000)
    
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
            self._load_graph_from_egif(egif_text, "Direct Input")
            self._add_to_history(egif_text, "Direct Input", 'egif')
            
    def _load_graph_from_egif(self, egif_text: str, source_name: str):
        """Load and display graph from EGIF text."""
        try:
            # Parse EGIF to EGI
            parser = EGIFParser(egif_text)
            egi = parser.parse()
            self._load_graph_from_egi(egi, source_name)
            
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse EGIF:\n{e}")
            self.status_bar.showMessage(f"Parse error: {e}")
            
    def _load_graph_from_egi(self, egi, source_name: str):
        """Load and display graph from EGI."""
        try:
            self.current_egi = egi
            
            # Parse and create EGDF
            # For now, create minimal layout - this will be enhanced
            layout_result = type('LayoutResult', (), {
                'vertex_positions': {v.id: (100 + i * 50, 100) for i, v in enumerate(egi.V)},
                'edge_positions': {e.id: (200 + i * 50, 150) for i, e in enumerate(egi.E)},
                'cut_bounds': {c.id: (50 + i * 100, 50, 150 + i * 100, 150) for i, c in enumerate(egi.Cut)}
            })()
            
            # Create EGDF document
            spatial_primitives = self._extract_spatial_primitives(layout_result)
            self.current_egdf = self.egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
            
            # Update all displays
            self._update_visual_display(layout_result)
            self._update_structure_display(egi)
            self._update_egif_display(egi)
            self._update_egdf_display(self.current_egdf)
            
            # Emit signals
            self.graph_selected.emit(egi)
            
            self.status_bar.showMessage(f"Loaded: {source_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load graph:\n{e}")
            self.status_bar.showMessage(f"Load error: {e}")
            
    def _extract_spatial_primitives(self, layout_result: LayoutResult) -> List[Dict]:
        """Extract spatial primitives from layout result."""
        primitives = []
        
        # Add vertices
        for vertex_id, position in layout_result.vertex_positions.items():
            primitives.append({
                'element_id': vertex_id,
                'element_type': 'vertex',
                'position': position,
                'bounds': (position[0]-10, position[1]-10, position[0]+10, position[1]+10)
            })
            
        # Add edges
        for edge_id, position in layout_result.edge_positions.items():
            primitives.append({
                'element_id': edge_id,
                'element_type': 'predicate',
                'position': position,
                'bounds': (position[0]-20, position[1]-10, position[0]+20, position[1]+10)
            })
            
        # Add cuts
        for cut_id, bounds in layout_result.cut_bounds.items():
            center = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
            primitives.append({
                'element_id': cut_id,
                'element_type': 'cut',
                'position': center,
                'bounds': bounds
            })
            
        return primitives
        
    def _update_visual_display(self, layout_result: LayoutResult):
        """Update the visual display."""
        if self.current_egi:
            # Create minimal layout for rendering
            layout_result = type('LayoutResult', (), {
                'vertex_positions': {v.id: (100 + i * 50, 100) for i, v in enumerate(self.current_egi.V)},
                'edge_positions': {e.id: (200 + i * 50, 150) for i, e in enumerate(self.current_egi.E)},
                'cut_bounds': {c.id: (50 + i * 100, 50, 150 + i * 100, 150) for i, c in enumerate(self.current_egi.Cut)}
            })()
            # Note: Renderer integration will be enhanced in next phase
            # self.renderer.render_egi(self.current_egi, layout_result, self.canvas)
            
    def _update_structure_display(self, egi):
        """Update the structure display."""
        structure_text = f"Vertices: {len(egi.V)}\n"
        structure_text += f"Edges: {len(egi.E)}\n"
        structure_text += f"Cuts: {len(egi.Cut)}\n\n"
        
        structure_text += "Vertices:\n"
        for vertex in egi.V:
            structure_text += f"  {vertex.id}: {vertex.label}\n"
            
        structure_text += "\nEdges:\n"
        for edge in egi.E:
            structure_text += f"  {edge.id}: {edge.predicate}\n"
            
        structure_text += "\nCuts:\n"
        for cut in egi.Cut:
            structure_text += f"  {cut.id}: contains {len(cut.enclosed_elements)} elements\n"
            
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
            vertex_labels = [v.label for v in edge.vertices]
            elements.append(f"({edge.predicate} {' '.join(vertex_labels)})")
            
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
                if hasattr(edge, 'label') and edge.label:
                    lines.append(f"{edge.label}({', '.join(str(v) for v in edge.vertices)})")
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
                self.renderer.export_png(self.canvas, file_path)
                self.status_bar.showMessage(f"Exported PNG: {file_path}")
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
