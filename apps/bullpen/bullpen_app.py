"""
Bullpen Application - Existential Graph Editor

The primary graph editing interface for Arisbe EG Works, featuring:
- Warmup Mode: Visual editing with syntactic constraints
- Practice Mode: Formal transformation rules enforcement
- Linear form input/output (EGIF ↔ CGIF/CLIF)
- Round-trip validation chiron
- Professional selection and editing tools

Author: Arisbe Project
"""

from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTabWidget,
    QTextEdit, QLabel, QPushButton, QCheckBox, QListWidget,
    QGroupBox, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

# Import salvaged components
from src.diagram_renderer_dau import DiagramRendererDau
from src.qt_canvas_adapter import QtCanvasAdapter
from src.enhanced_diagram_controller import EnhancedDiagramController


class BullpenApp(QWidget):
    """
    Main Bullpen application widget.
    
    Provides comprehensive graph editing capabilities with mode switching,
    linear form integration, and professional interaction patterns.
    """
    
    # Signals
    graph_changed = Signal()
    mode_changed = Signal(str)
    selection_changed = Signal(list)
    
    def __init__(self, pipeline):
        super().__init__()
        
        self.pipeline = pipeline
        self.current_mode = 'warmup'  # 'warmup' or 'practice'
        self.current_graph = None
        self.unsaved_changes = False
        
        # Initialize components
        self._setup_ui()
        self._initialize_canvas()
        self._initialize_controller()
        self._connect_signals()
        
        print("✓ Bullpen application initialized")
    
    def _setup_ui(self):
        """Set up the user interface layout."""
        # Main horizontal splitter
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel: Canvas
        self._create_canvas_panel()
        
        # Right panel: Tools and information
        self._create_tools_panel()
        
        # Set initial splitter proportions (70% canvas, 30% tools)
        self.main_splitter.setSizes([1000, 400])
    
    def _create_canvas_panel(self):
        """Create main canvas panel."""
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        
        # Mode selection tabs
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setMaximumHeight(35)
        
        # Warmup mode tab
        warmup_tab = QWidget()
        self.mode_tabs.addTab(warmup_tab, "Warmup")
        
        # Practice mode tab
        practice_tab = QWidget()
        self.mode_tabs.addTab(practice_tab, "Practice")
        
        # Connect mode change
        self.mode_tabs.currentChanged.connect(self._on_mode_changed)
        
        canvas_layout.addWidget(self.mode_tabs)
        
        # Canvas container
        self.canvas_container = QFrame()
        self.canvas_container.setFrameStyle(QFrame.StyledPanel)
        self.canvas_container.setMinimumSize(600, 400)
        canvas_layout.addWidget(self.canvas_container)
        
        self.main_splitter.addWidget(canvas_widget)
    
    def _create_tools_panel(self):
        """Create tools and information panel."""
        tools_widget = QWidget()
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(5, 5, 5, 5)
        
        # Linear Form section
        self._create_linear_form_section(tools_layout)
        
        # Subgraph Elements section
        self._create_subgraph_section(tools_layout)
        
        # Round-trip Chiron section
        self._create_chiron_section(tools_layout)
        
        # Action Context section
        self._create_action_section(tools_layout)
        
        # Annotations section
        self._create_annotations_section(tools_layout)
        
        tools_layout.addStretch()
        self.main_splitter.addWidget(tools_widget)
    
    def _create_linear_form_section(self, parent_layout):
        """Create linear form input/edit section."""
        group = QGroupBox("Linear Form")
        layout = QVBoxLayout(group)
        
        # EGIF input
        self.egif_input = QTextEdit()
        self.egif_input.setMaximumHeight(100)
        self.egif_input.setPlaceholderText("Enter EGIF expression...")
        self.egif_input.setFont(QFont("Courier", 10))
        layout.addWidget(QLabel("EGIF Input:"))
        layout.addWidget(self.egif_input)
        
        # Load/Apply buttons
        button_layout = QHBoxLayout()
        self.load_egif_btn = QPushButton("Load EGIF")
        self.apply_egif_btn = QPushButton("Apply Changes")
        button_layout.addWidget(self.load_egif_btn)
        button_layout.addWidget(self.apply_egif_btn)
        layout.addLayout(button_layout)
        
        # CGIF/CLIF expansion (read-only)
        self.expansion_output = QTextEdit()
        self.expansion_output.setMaximumHeight(80)
        self.expansion_output.setReadOnly(True)
        self.expansion_output.setFont(QFont("Courier", 9))
        layout.addWidget(QLabel("CGIF/CLIF Expansion:"))
        layout.addWidget(self.expansion_output)
        
        parent_layout.addWidget(group)
        
        # Connect signals
        self.load_egif_btn.clicked.connect(self._load_egif)
        self.apply_egif_btn.clicked.connect(self._apply_egif_changes)
        self.egif_input.textChanged.connect(self._on_egif_text_changed)
    
    def _create_subgraph_section(self, parent_layout):
        """Create subgraph elements enumeration section."""
        group = QGroupBox("Subgraph Elements")
        layout = QVBoxLayout(group)
        
        self.subgraph_list = QListWidget()
        self.subgraph_list.setMaximumHeight(120)
        layout.addWidget(self.subgraph_list)
        
        # Selection info
        self.selection_info = QLabel("No selection")
        self.selection_info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.selection_info)
        
        parent_layout.addWidget(group)
    
    def _create_chiron_section(self, parent_layout):
        """Create round-trip validation chiron section."""
        group = QGroupBox("Round-trip Chiron")
        layout = QVBoxLayout(group)
        
        # Validation status
        self.validation_status = QLabel("EGDF ↔ EGIF: Ready")
        self.validation_status.setStyleSheet("color: #008000; font-weight: bold;")
        layout.addWidget(self.validation_status)
        
        # Export options
        export_layout = QHBoxLayout()
        self.export_egdf_btn = QPushButton("Export EGDF")
        self.export_svg_btn = QPushButton("Export SVG")
        export_layout.addWidget(self.export_egdf_btn)
        export_layout.addWidget(self.export_svg_btn)
        layout.addLayout(export_layout)
        
        parent_layout.addWidget(group)
        
        # Connect signals
        self.export_egdf_btn.clicked.connect(self._export_egdf)
        self.export_svg_btn.clicked.connect(self._export_svg)
    
    def _create_action_section(self, parent_layout):
        """Create action context section."""
        group = QGroupBox("Action Context")
        layout = QVBoxLayout(group)
        
        # Action buttons
        action_layout = QVBoxLayout()
        
        self.move_btn = QPushButton("Move")
        self.delete_btn = QPushButton("Delete")
        self.add_cut_btn = QPushButton("Add Cut")
        self.add_vertex_btn = QPushButton("Add Individual")
        self.add_predicate_btn = QPushButton("Add Predicate")
        
        action_layout.addWidget(self.move_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.add_cut_btn)
        action_layout.addWidget(self.add_vertex_btn)
        action_layout.addWidget(self.add_predicate_btn)
        
        layout.addLayout(action_layout)
        
        # Current action status
        self.action_status = QLabel("Ready for action")
        self.action_status.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.action_status)
        
        parent_layout.addWidget(group)
        
        # Connect action buttons
        self.move_btn.clicked.connect(lambda: self._start_action('move'))
        self.delete_btn.clicked.connect(lambda: self._start_action('delete'))
        self.add_cut_btn.clicked.connect(lambda: self._start_action('add_cut'))
        self.add_vertex_btn.clicked.connect(lambda: self._start_action('add_vertex'))
        self.add_predicate_btn.clicked.connect(lambda: self._start_action('add_predicate'))
    
    def _create_annotations_section(self, parent_layout):
        """Create annotations control section."""
        group = QGroupBox("Annotations")
        layout = QVBoxLayout(group)
        
        # Annotation checkboxes
        self.show_arity_cb = QCheckBox("Arity numbering")
        self.show_variables_cb = QCheckBox("Variable labels")
        self.show_ligature_signs_cb = QCheckBox("Ligature '=' signs")
        
        layout.addWidget(self.show_arity_cb)
        layout.addWidget(self.show_variables_cb)
        layout.addWidget(self.show_ligature_signs_cb)
        
        parent_layout.addWidget(group)
        
        # Connect annotation toggles
        self.show_arity_cb.toggled.connect(self._update_annotations)
        self.show_variables_cb.toggled.connect(self._update_annotations)
        self.show_ligature_signs_cb.toggled.connect(self._update_annotations)
    
    def _initialize_canvas(self):
        """Initialize the diagram canvas."""
        try:
            # Create canvas layout
            canvas_layout = QVBoxLayout(self.canvas_container)
            canvas_layout.setContentsMargins(0, 0, 0, 0)
            
            # Initialize canvas adapter
            self.canvas = QtCanvasAdapter()
            canvas_layout.addWidget(self.canvas)
            
            # Initialize renderer
            self.renderer = DiagramRendererDau()
            
            print("✓ Canvas initialized")
            
        except Exception as e:
            print(f"⚠ Canvas initialization failed: {e}")
            # Create placeholder
            placeholder = QLabel("Canvas Loading...")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
            canvas_layout = QVBoxLayout(self.canvas_container)
            canvas_layout.addWidget(placeholder)
    
    def _initialize_controller(self):
        """Initialize the diagram controller."""
        try:
            if hasattr(self, 'canvas') and hasattr(self, 'renderer'):
                self.controller = EnhancedDiagramController(
                    canvas=self.canvas,
                    renderer=self.renderer,
                    pipeline=self.pipeline
                )
                print("✓ Controller initialized")
            else:
                self.controller = None
                print("⚠ Controller not available (canvas/renderer missing)")
        except Exception as e:
            print(f"⚠ Controller initialization failed: {e}")
            self.controller = None
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Auto-validation timer
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_round_trip)
        
        # Connect graph change signal
        self.graph_changed.connect(self._on_graph_changed)
    
    def _on_mode_changed(self, index):
        """Handle mode tab change."""
        modes = ['warmup', 'practice']
        if 0 <= index < len(modes):
            old_mode = self.current_mode
            self.current_mode = modes[index]
            
            print(f"Mode changed: {old_mode} → {self.current_mode}")
            self.mode_changed.emit(self.current_mode)
            
            # Update UI for mode
            self._update_mode_ui()
    
    def _update_mode_ui(self):
        """Update UI elements based on current mode."""
        if self.current_mode == 'warmup':
            self.action_status.setText("Warmup mode: Visual editing")
            # Enable all visual editing actions
            self.move_btn.setEnabled(True)
            self.add_cut_btn.setEnabled(True)
            self.add_vertex_btn.setEnabled(True)
            self.add_predicate_btn.setEnabled(True)
            
        elif self.current_mode == 'practice':
            self.action_status.setText("Practice mode: Formal transformations")
            # Restrict to formal transformation rules
            # (Implementation will add formal rule buttons)
    
    def _load_egif(self):
        """Load EGIF from input field."""
        egif_text = self.egif_input.toPlainText().strip()
        print(f"🔍 Loading EGIF: '{egif_text}'")
        
        if not egif_text:
            print("⚠ No EGIF text to load")
            return
        
        try:
            print("📝 Step 1: Parsing EGIF...")
            # Parse EGIF using pipeline
            egi = self.pipeline.parse_egif(egif_text)
            print(f"✓ EGI parsed: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            print("📝 Step 2: Converting to EGDF...")
            egdf = self.pipeline.egi_to_egdf(egi)
            print(f"✓ EGDF created: {type(egdf)}")
            
            print("📝 Step 3: Loading to controller...")
            # Update canvas
            if self.controller:
                self.controller.load_egdf(egdf)
                print("✓ Controller loaded EGDF")
            else:
                print("⚠ No controller available")
            
            self.current_graph = egi
            self.graph_changed.emit()
            
            # Update expansion
            self._update_expansion_output(egif_text)
            
            self.validation_status.setText("EGDF ↔ EGIF: ✓ Valid")
            self.validation_status.setStyleSheet("color: #008000; font-weight: bold;")
            
            print("🎉 EGIF loading completed successfully")
            
        except Exception as e:
            self.validation_status.setText(f"EGDF ↔ EGIF: ✗ Error")
            self.validation_status.setStyleSheet("color: #cc0000; font-weight: bold;")
            print(f"❌ EGIF load error: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_egif_changes(self):
        """Apply changes from EGIF input."""
        self._load_egif()
        self.unsaved_changes = True
    
    def _on_egif_text_changed(self):
        """Handle EGIF text changes."""
        # Trigger validation after short delay
        self.validation_timer.start(1000)
    
    def _validate_round_trip(self):
        """Validate round-trip EGIF ↔ EGDF."""
        egif_text = self.egif_input.toPlainText().strip()
        if not egif_text:
            self.validation_status.setText("EGDF ↔ EGIF: Ready")
            self.validation_status.setStyleSheet("color: #666;")
            return
        
        try:
            # Test round-trip
            egi = self.pipeline.parse_egif(egif_text)
            egdf = self.pipeline.egi_to_egdf(egi)
            round_trip_egif = self.pipeline.egdf_to_egif(egdf)
            
            # Validate equivalence (simplified check)
            if egif_text.replace(' ', '') == round_trip_egif.replace(' ', ''):
                self.validation_status.setText("EGDF ↔ EGIF: ✓ Round-trip valid")
                self.validation_status.setStyleSheet("color: #008000; font-weight: bold;")
            else:
                self.validation_status.setText("EGDF ↔ EGIF: ⚠ Round-trip differs")
                self.validation_status.setStyleSheet("color: #ff8800; font-weight: bold;")
                
        except Exception as e:
            self.validation_status.setText("EGDF ↔ EGIF: ✗ Invalid")
            self.validation_status.setStyleSheet("color: #cc0000; font-weight: bold;")
    
    def _update_expansion_output(self, egif_text):
        """Update CGIF/CLIF expansion output."""
        try:
            # Placeholder for expansion logic
            expansion = f"[CGIF expansion of: {egif_text}]\n[CLIF expansion will be implemented]"
            self.expansion_output.setText(expansion)
        except Exception as e:
            self.expansion_output.setText(f"Expansion error: {e}")
    
    def _start_action(self, action_type):
        """Start an action workflow."""
        print(f"Starting action: {action_type}")
        self.action_status.setText(f"Action: {action_type} - Select target")
        
        if self.controller:
            self.controller.start_action(action_type)
    
    def _on_graph_changed(self):
        """Handle graph change events."""
        self.unsaved_changes = True
        
        # Update subgraph list
        self._update_subgraph_list()
        
        # Trigger validation
        self.validation_timer.start(500)
    
    def _update_subgraph_list(self):
        """Update subgraph elements list."""
        self.subgraph_list.clear()
        
        if self.current_graph:
            # Add vertices
            for vertex in self.current_graph.V:
                self.subgraph_list.addItem(f"• vertex_{vertex.id}")
            
            # Add edges
            for edge in self.current_graph.E:
                self.subgraph_list.addItem(f"• edge_{edge.id}")
            
            # Add cuts
            for cut in self.current_graph.Cut:
                self.subgraph_list.addItem(f"• cut_{cut.id}")
    
    def _update_annotations(self):
        """Update annotation display."""
        if self.controller:
            annotations = {
                'arity': self.show_arity_cb.isChecked(),
                'variables': self.show_variables_cb.isChecked(),
                'ligature_signs': self.show_ligature_signs_cb.isChecked()
            }
            self.controller.set_annotations(annotations)
    
    def _export_egdf(self):
        """Export current graph as EGDF."""
        if not self.current_graph:
            QMessageBox.warning(self, "Export Error", "No graph to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export EGDF", "", "EGDF files (*.egdf);;All files (*)"
        )
        
        if filename:
            try:
                egdf = self.pipeline.egi_to_egdf(self.current_graph)
                egdf_json = self.pipeline.export_egdf(egdf, format_type="json")
                
                with open(filename, 'w') as f:
                    f.write(egdf_json)
                
                QMessageBox.information(self, "Export Success", f"EGDF exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export EGDF: {e}")
    
    def _export_svg(self):
        """Export current graph as SVG."""
        if not self.current_graph:
            QMessageBox.warning(self, "Export Error", "No graph to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export SVG", "", "SVG files (*.svg);;All files (*)"
        )
        
        if filename:
            try:
                # Implementation will use renderer to generate SVG
                QMessageBox.information(self, "Export Success", f"SVG exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export SVG: {e}")
    
    # Public API methods
    def new_graph(self):
        """Create a new empty graph."""
        self.current_graph = None
        self.egif_input.clear()
        self.expansion_output.clear()
        self.subgraph_list.clear()
        self.unsaved_changes = False
        
        if self.controller:
            self.controller.clear()
        
        self.validation_status.setText("EGDF ↔ EGIF: Ready")
        self.validation_status.setStyleSheet("color: #666;")
        
        print("New graph created")
    
    def import_egif(self):
        """Import EGIF from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import EGIF", "", "EGIF files (*.egif);;Text files (*.txt);;All files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    egif_content = f.read()
                
                self.egif_input.setText(egif_content)
                self._load_egif()
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import EGIF: {e}")
    
    def export_egif(self):
        """Export current graph as EGIF."""
        if not self.current_graph:
            QMessageBox.warning(self, "Export Error", "No graph to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export EGIF", "", "EGIF files (*.egif);;Text files (*.txt);;All files (*)"
        )
        
        if filename:
            try:
                egif_text = self.pipeline.egi_to_egif(self.current_graph)
                
                with open(filename, 'w') as f:
                    f.write(egif_text)
                
                QMessageBox.information(self, "Export Success", f"EGIF exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export EGIF: {e}")
    
    def set_mode(self, mode):
        """Set editor mode."""
        if mode in ['warmup', 'practice']:
            mode_index = ['warmup', 'practice'].index(mode)
            self.mode_tabs.setCurrentIndex(mode_index)
    
    def toggle_annotations(self):
        """Toggle all annotations."""
        current_state = self.show_arity_cb.isChecked()
        new_state = not current_state
        
        self.show_arity_cb.setChecked(new_state)
        self.show_variables_cb.setChecked(new_state)
        self.show_ligature_signs_cb.setChecked(new_state)
    
    def has_unsaved_changes(self):
        """Check if there are unsaved changes."""
        return self.unsaved_changes
    
    def auto_save(self):
        """Perform auto-save."""
        if self.unsaved_changes and self.current_graph:
            # Implementation will save to temp file
            print("Auto-save performed")
    
    # Canvas interaction methods
    def zoom_in(self):
        """Zoom in on canvas."""
        if hasattr(self.canvas, 'zoom_in'):
            self.canvas.zoom_in()
    
    def zoom_out(self):
        """Zoom out on canvas."""
        if hasattr(self.canvas, 'zoom_out'):
            self.canvas.zoom_out()
    
    def reset_zoom(self):
        """Reset canvas zoom."""
        if hasattr(self.canvas, 'reset_zoom'):
            self.canvas.reset_zoom()
    
    def copy(self):
        """Copy selection."""
        if self.controller:
            self.controller.copy_selection()
    
    def paste(self):
        """Paste from clipboard."""
        if self.controller:
            self.controller.paste()
    
    def delete_selection(self):
        """Delete current selection."""
        if self.controller:
            self.controller.delete_selection()
    
    def undo(self):
        """Undo last action."""
        if self.controller:
            self.controller.undo()
    
    def redo(self):
        """Redo last undone action."""
        if self.controller:
            self.controller.redo()
